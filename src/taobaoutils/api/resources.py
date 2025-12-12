import json
from datetime import datetime

import pandas as pd
import requests
from flask_praetorian import auth_required, current_user
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from taobaoutils import config_data, logger
from taobaoutils.api.auth import api_token_required
from taobaoutils.app import db
from taobaoutils.models import ProductListing, RequestConfig


def _get_payload_from_listing(product_listing):
    """
    Helper function to generate payload from a ProductListing object.
    This logic is similar to process_row_logic.
    """
    url = product_listing.product_link
    payload_template = config_data["request_payload_template"]

    current_payload = json.loads(json.dumps(payload_template))  # Deep copy

    if "linkData" in current_payload and isinstance(current_payload["linkData"], list) and current_payload["linkData"]:
        num_iid = ""
        try:
            if "id=" in url:
                num_iid = url.split("id=")[1].split("&")[0]
        except Exception:
            logger.warning("无法从URL '%s' 中提取商品ID。", url)

        if current_payload["linkData"][0]["url"] == "{url}":
            current_payload["linkData"][0]["url"] = url

        current_payload["linkData"][0]["num_iid"] = (
            num_iid if num_iid else current_payload["linkData"][0].get("num_iid", "")
        )

    return current_payload


def _send_single_task_to_scheduler(product_listing):
    """
    Sends a single product listing task to the scheduler service.
    """
    scheduler_url = config_data["scheduler"]["SCHEDULER_SERVICE_URL"]

    task_url = scheduler_url.rstrip("/") + "/add_req_task"

    payload = _get_payload_from_listing(product_listing)
    cookie = config_data.get("custom_headers", {})

    req_config = product_listing.request_config
    if req_config:
        target_url = req_config.request_url
        request_interval_minutes = req_config.request_interval_minutes
        random_min = req_config.random_min
        random_max = req_config.random_max
    else:
        # Should not happen if validation works, but safe default or error?
        # User said "not needed", implying we trust it exists.
        # But `lazy=True` might mean we need to ensure it's loaded? No, SQLAlchemy handles it.
        # I'll log a warning if missing and return False or just let it fail?
        # User said "not needed", so I will assume it is present. But to be safe against AttributeError if somehow None,
        # I will leave a guard but NO fallback to config_data.
        logger.error("ProductListing %s missing request_config!", product_listing.id)
        return False

    task_data = {
        "cookie": cookie,
        "payload": payload,
        "target_url": target_url,
        "request_interval_minutes": request_interval_minutes,
        "random_min": random_min,
        "random_max": random_max,
        "send_time": datetime.utcnow().timestamp(),
    }

    try:
        response = requests.post(task_url, json=task_data, timeout=10)
        response.raise_for_status()
        logger.info("Successfully sent single task to scheduler for listing ID: %s", product_listing.id)
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Failed to send single task to scheduler for listing ID %s: %s", product_listing.id, e)
        return False


def _send_batch_tasks_to_scheduler(product_listings):
    """
    Sends a batch of product listing tasks to the scheduler service.
    """
    scheduler_url = config_data["scheduler"]["SCHEDULER_SERVICE_URL"]
    callback_url = config_data.get("scheduler", {}).get("CALLBACK_URL")

    task_url = scheduler_url.rstrip("/") + "/add_req_tasks"

    tasks_data = []

    for listing in product_listings:
        if not listing.request_config:
            logger.warning("ProductListing %s missing request_config, skipping.", listing.id)
            continue

        req_config = listing.request_config

        # Prepare parameters for template substitution
        params = {
            "title": listing.title or "",
            "product_link": listing.product_link or "",
            "product_id": listing.product_id or "",
            "stock": listing.stock or 0,
            "listing_code": listing.listing_code or "",
            "id": listing.id,
            "user_id": listing.user_id,
        }

        # Helper function to substitute and parse JSON
        def process_template(template_str, params):
            if not template_str:
                return None
            try:
                # Use simple string replacement to avoid str.format's issues with JSON braces
                substituted_str = template_str
                for key, value in params.items():
                    # Handle None/Types
                    val_str = str(value) if value is not None else ""
                    # Escape quotes if necessary? JSON string values are usually quoted.
                    # If placeholder is inside quotes: "url": "{url}" -> "url": "http://..."
                    # If placeholder is raw: "count": {stock} -> "count": 10
                    # For now, simple replace.
                    substituted_str = substituted_str.replace(f"{{{key}}}", val_str)

                return json.loads(substituted_str)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Failed to process template for RequestConfig %s: %s", req_config.id, e)
                return None

        header = process_template(req_config.header, params)
        body = process_template(req_config.payload, params)

        task_item = {
            "name": listing.title or f"Product {listing.id}",
            "start_time": datetime.utcnow().timestamp(),
            "header": header,
            "method": "GET",
            "request_url": scheduler_url,  # Per user instruction
            "callback_url": callback_url,
            "callback_id": str(listing.id),
            "callback_token": "",
            "body": body,
            "cron": None,
        }
        tasks_data.append(task_item)

    if not tasks_data:
        logger.warning("No valid tasks to send to scheduler.")
        return False

    payload = {"tasks_data": tasks_data}

    try:
        response = requests.post(task_url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info("Successfully sent batch of %d tasks to scheduler.", len(tasks_data))
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Failed to send batch tasks to scheduler: %s", e)
        return False


class ProductListingResource(Resource):  # Renamed class
    @auth_required
    def get(self, log_id=None):
        user_id = current_user().id  # Get current user's ID
        if log_id:
            # Changed RequestLog to ProductListing and added user_id filter
            log = ProductListing.query.filter_by(id=log_id, user_id=user_id).first_or_404()
            return log.to_dict()
        else:
            # Changed RequestLog to ProductListing and added user_id filter
            logs = ProductListing.query.filter_by(user_id=user_id).order_by(ProductListing.send_time.desc()).all()
            return [log.to_dict() for log in logs]

    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("request_config_id", type=int, required=True, help="RequestConfig ID is required")
        parser.add_argument("status", type=str, required=False, help="Status")  # Made optional
        parser.add_argument("response_content", type=str, required=False)
        parser.add_argument("response_code", type=int, required=False)
        parser.add_argument("product_id", type=str, required=False)
        parser.add_argument("product_link", type=str, required=False)
        parser.add_argument("title", type=str, required=False)
        parser.add_argument("stock", type=int, required=False)
        parser.add_argument("listing_code", type=str, required=False)

        args = parser.parse_args()

        # Check if request_config exists
        req_config = RequestConfig.query.filter_by(id=args["request_config_id"], user_id=current_user().id).first()
        if not req_config:
            return {"message": "Invalid request_config_id"}, 400

        # Changed RequestLog to ProductListing
        new_listing = ProductListing(
            user_id=current_user().id,
            request_config_id=args["request_config_id"],
            status=args["status"],
            send_time=datetime.utcnow(),
            response_content=args["response_content"],
            response_code=args["response_code"],
            product_id=args["product_id"],
            product_link=args["product_link"],
            title=args["title"],
            stock=args["stock"],
            listing_code=args["listing_code"],
        )
        db.session.add(new_listing)
        db.session.commit()
        logger.info(
            "New product listing added for user %s: %s",
            current_user().id,
            new_listing.product_id or new_listing.product_link,
        )  # Updated to use product_link

        # After successfully adding to DB, send to scheduler service
        if _send_single_task_to_scheduler(new_listing):
            new_listing.status = "是否完成"  # Set status to "whether completed"
            db.session.commit()
            logger.info("Product listing %s status updated to '是否完成' after sending to scheduler.", new_listing.id)
        else:
            logger.warning(
                "Product listing %s failed to send to scheduler service. Status remains as before.", new_listing.id
            )

        return new_listing.to_dict(), 201


class ExcelUploadResource(Resource):
    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("file", type=FileStorage, location="files", required=True, help="Excel file is required")
        parser.add_argument(
            "request_config_id", type=int, location="form", required=True, help="RequestConfig ID is required"
        )  # Add request_config_id
        args = parser.parse_args()

        excel_file = args["file"]
        request_config_id = args["request_config_id"]

        # Validate request_config_id
        req_config = RequestConfig.query.filter_by(id=request_config_id, user_id=current_user().id).first()
        if not req_config:
            return {"message": "Invalid request_config_id"}, 400

        if not excel_file.filename.endswith((".xlsx", ".xls")):
            return {"message": "Invalid file type. Only .xlsx and .xls are allowed."}, 400

        try:
            df = pd.read_excel(excel_file.stream)

            required_headers = {
                "商品ID": "product_id",
                "商品链接": "product_link",
                "标题": "title",
                "库存": "stock",
                "上架编码": "listing_code",
            }

            # Validate headers
            if not all(header in df.columns for header in required_headers.keys()):
                missing_headers = [header for header in required_headers.keys() if header not in df.columns]
                return {"message": f"Missing required Excel headers: {', '.join(missing_headers)}"}, 400

            new_listings = []
            for _, row in df.iterrows():
                new_listing = ProductListing(
                    user_id=current_user().id,
                    request_config_id=request_config_id,
                    product_id=str(row["商品ID"]) if pd.notna(row["商品ID"]) else None,
                    product_link=str(row["商品链接"]) if pd.notna(row["商品链接"]) else None,
                    title=str(row["标题"]) if pd.notna(row["标题"]) else None,
                    stock=int(row["库存"]) if pd.notna(row["库存"]) else None,
                    listing_code=str(row["上架编码"]) if pd.notna(row["上架编码"]) else None,
                    send_time=datetime.utcnow(),  # Default send_time
                    status="Uploaded",  # Default status for uploaded items
                )
                db.session.add(new_listing)
                new_listings.append(new_listing)

            db.session.commit()  # Commit all new listings

            # After committing, send each new listing to the scheduler service
            if _send_batch_tasks_to_scheduler(new_listings):
                for listing in new_listings:
                    listing.status = "是否完成"  # Set status to "whether completed"
                    db.session.add(listing)  # Re-add to session for update
                db.session.commit()  # Commit status updates
                logger.info(
                    "Batch of %d product listings status updated to '是否完成' after sending to scheduler.",
                    len(new_listings),
                )
            else:
                logger.warning(
                    "Batch of %d product listings from Excel failed to send to scheduler service. Status remains as before.",
                    len(new_listings),
                )

            logger.info(
                "Successfully uploaded and processed %d product listings from Excel for user %s.",
                len(new_listings),
                current_user().id,
            )
            return {"message": f"Successfully uploaded and processed {len(new_listings)} product listings."}, 201

        except Exception as e:
            db.session.rollback()
            logger.error("Error processing Excel upload: %s", str(e))
            return {"message": f"Error processing Excel file: {str(e)}"}, 500


class SchedulerCallbackResource(Resource):
    @api_token_required
    def post(self):
        """
        处理scheduler_service的回调请求，更新ProductListing的状态、响应内容和响应码
        接收参数：id (int)、status (str)、response_code (int)、response_content (str)
        需要使用API token进行认证访问
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, required=True, help="ProductListing ID is required")
        parser.add_argument("status", type=str, required=True, help="Status is required")
        parser.add_argument("response_code", type=int, required=False, help="HTTP response code")
        parser.add_argument("response_content", type=str, required=False, help="HTTP response content")
        args = parser.parse_args()

        try:
            # 通过id查询ProductListing
            product_listing = ProductListing.query.filter_by(id=args["id"]).first()
            if not product_listing:
                logger.warning("ProductListing with ID %d not found.", args["id"])
                return {"message": "Product listing not found"}, 404

            # 更新状态、响应码和响应内容
            product_listing.status = args["status"]

            # 只有当提供了response_code和response_content时才更新
            if args["response_code"] is not None:
                product_listing.response_code = args["response_code"]

            if args["response_content"] is not None:
                product_listing.response_content = args["response_content"]

            # 更新时间
            product_listing.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(
                "ProductListing %d updated - Status: '%s', Response Code: %s by user %s",
                args["id"],
                args["status"],
                args.get("response_code", "N/A"),
                product_listing.user_id,
            )

            return {"message": "Status and response information updated successfully"}, 200
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating ProductListing %d: %s", args["id"], str(e))
            return {"message": "Internal server error"}, 500
