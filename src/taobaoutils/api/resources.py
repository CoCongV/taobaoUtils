from flask_restful import Resource, reqparse
from flask_praetorian import auth_required
from taobaoutils.app import db
from taobaoutils.models import ProductListing, User # Renamed RequestLog to ProductListing
from taobaoutils import config_data, logger
from datetime import datetime
from werkzeug.datastructures import FileStorage # Added for file uploads
import pandas as pd # Added for Excel processing


class ProductListingResource(Resource): # Renamed class
    @auth_required
    def get(self, log_id=None):
        if log_id:
            # Changed RequestLog to ProductListing
            log = ProductListing.query.get_or_404(log_id) 
            return log.to_dict()
        else:
            # Changed RequestLog to ProductListing
            logs = ProductListing.query.order_by(ProductListing.send_time.desc()).all()
            return [log.to_dict() for log in logs]

    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=False, help='Status') # Made optional
        parser.add_argument('response_content', type=str, required=False)
        parser.add_argument('response_code', type=int, required=False)
        parser.add_argument('product_id', type=str, required=False)
        parser.add_argument('product_link', type=str, required=False)
        parser.add_argument('title', type=str, required=False)
        parser.add_argument('stock', type=int, required=False)
        parser.add_argument('listing_code', type=str, required=False)

        args = parser.parse_args()

        # Changed RequestLog to ProductListing
        new_listing = ProductListing(
            # Removed url=args['url']
            status=args['status'],
            send_time=datetime.utcnow(),
            response_content=args['response_content'],
            response_code=args['response_code'],
            product_id=args['product_id'],
            product_link=args['product_link'],
            title=args['title'],
            stock=args['stock'],
            listing_code=args['listing_code']
        )
        db.session.add(new_listing)
        db.session.commit()
        logger.info("New product listing added: %s", new_listing.product_id or new_listing.product_link) # Updated to use product_link
        return new_listing.to_dict(), 201


class ExcelUploadResource(Resource):
    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files', required=True, help='Excel file is required')
        args = parser.parse_args()
        
        excel_file = args['file']
        
        if not excel_file.filename.endswith(('.xlsx', '.xls')):
            return {'message': 'Invalid file type. Only .xlsx and .xls are allowed.'}, 400
        
        try:
            df = pd.read_excel(excel_file.stream)
            
            required_headers = {
                '商品ID': 'product_id',
                '商品链接': 'product_link',
                '标题': 'title',
                '库存': 'stock',
                '上架编码': 'listing_code'
            }
            
            # Validate headers
            if not all(header in df.columns for header in required_headers.keys()):
                missing_headers = [header for header in required_headers.keys() if header not in df.columns]
                return {'message': f'Missing required Excel headers: {", ".join(missing_headers)}'}, 400
            
            new_listings = []
            for index, row in df.iterrows():
                new_listing = ProductListing(
                    product_id=str(row[required_headers['商品ID']]) if pd.notna(row[required_headers['商品ID']]) else None,
                    product_link=str(row[required_headers['商品链接']]) if pd.notna(row[required_headers['商品链接']]) else None,
                    title=str(row[required_headers['标题']]) if pd.notna(row[required_headers['标题']]) else None,
                    stock=int(row[required_headers['库存']]) if pd.notna(row[required_headers['库存']]) else None,
                    listing_code=str(row[required_headers['上架编码']]) if pd.notna(row[required_headers['上架编码']]) else None,
                    send_time=datetime.utcnow(), # Default send_time
                    status="Uploaded" # Default status for uploaded items
                )
                db.session.add(new_listing)
                new_listings.append(new_listing)
            
            db.session.commit()
            logger.info("Successfully uploaded and processed %d product listings from Excel.", len(new_listings))
            return {'message': f'Successfully uploaded and processed {len(new_listings)} product listings.'}, 201
            
        except Exception as e:
            db.session.rollback()
            logger.error("Error processing Excel upload: %s", str(e))
            return {'message': f'Error processing Excel file: {str(e)}'}, 500