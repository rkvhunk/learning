import sys,os
import configparser, json
from flask import g, Flask
from multiprocessing import Pool
if '/app/entityextractor/core_backend/build_solutions' in sys.path:
    sys.path.remove('/app/entityextractor/core_backend/build_solutions')
sys.path.append(r'../')
sys.path.append(r'../manager/')
from core_backend.manager.handler import Handler
from core_backend.base import Session
from datetime import datetime
from core_backend.database.models.model import File, Solution
from core_backend.utility.app_constants import ASPECT_UI_ROUTES
from core_backend.utility.utility_application import update_file_status, update_exec_time, update_status_time, notification_alert
from core_backend.utility.notification_messages import document_execution_started, document_execution_completed
sol_id = sys.argv[2]
handler = Handler()
def processing(file_id):
    start = datetime.now().timestamp()
    # session = Session()
    update_file_status(file_id, 12)
    update_status_time(file_id, datetime.now().timestamp(), 10)
    g.db_session.commit()
    file_sol_detail = g.db_session.query(File.name, Solution.name.label('sol_name'), File.entry_point, File.user_name).join(Solution).filter(File.file_id == file_id).first()
    headers = {"X-Auth-Userid": file_sol_detail.user_name, "X-Auth-Username":file_sol_detail.user_name, "X-Auth-Email": file_sol_detail.user_name}
    resp = notification_alert("Document",document_execution_started.format(document_names=file_sol_detail.name,solution_name=file_sol_detail.sol_name),ASPECT_UI_ROUTES['online_batch'], [file_sol_detail.user_name],{'solution_id': sol_id, 'batch_type': file_sol_detail.entry_point, 'file_id': file_id},headers, "document", file_sol_detail.user_name, sol_id, file_id)
    op = 'NA'
    op = handler.text_extraction_handler(type_of_method="GOOGLE_VISION",multi_language="[]",provider="google_textract",page_layout="",bounding_box="{}",zoning="{'remove_non_english': False, 'rerun': False, 'tokenizer': 'False', 'tolerance_factor': 2, 'zoning': False}",with_coordinates="False",coordinate_level="['word_level']",classes="[]",op=op,file_id=file_id,sol_id=sol_id)

    # session = Session()
    # session = Session()
    end = datetime.now().timestamp()
    update_status_time(file_id, end-start, 'exec_time')
    update_file_status(file_id, 15)
    update_status_time(file_id, datetime.now().timestamp(), 13)
    resp = notification_alert("Document",document_execution_completed.format(document_names=file_sol_detail.name,solution_name=file_sol_detail.sol_name),ASPECT_UI_ROUTES['online_batch'], [file_sol_detail.user_name],{'solution_id': sol_id, 'batch_type': file_sol_detail.entry_point, 'file_id': file_id},headers, "document", file_sol_detail.user_name, sol_id, file_id)
    g.db_session.commit()
    g.db_session.close()

def run(input_files):
    config = configparser.ConfigParser()
    config_path = "config" + os.sep + "config.properties"
    config.read(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_path))
    pool = Pool(int(config['Pipeline']['num_of_cores']))
    pool.map(processing, input_files)
    pool.close()
    pool.join()

if __name__ == '__main__':
    input_files = sys.argv[1].split(',')
    tenant_metadata = json.loads(sys.argv[3])
    app = Flask('TextExtractFrameworkPipeline')
    with app.app_context():
        session = Session()
        g.db_session = session
        g.tenant_metadata = tenant_metadata
        if tenant_metadata and tenant_metadata.get('database_schema'):
            g.db_session.connection(execution_options={"schema_translate_map": {DEFAULT_SCHEMA_NAME: tenant_metadata['database_schema']}})
        run(input_files)

