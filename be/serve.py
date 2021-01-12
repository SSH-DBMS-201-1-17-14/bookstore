import logging
import os
from flask import Flask
from flask import Blueprint
from flask import request
from be.view import auth
from be.view import seller
from be.view import buyer
from be.model.store import init_database
from apscheduler.schedulers.background import BackgroundScheduler
# from be.model.global_scheduler import instance_GlobalAutoCancelOrder,GlobalAutoCancelOrder
import be.model.global_scheduler as global_scheduler
import psycopg2

bp_shutdown = Blueprint("shutdown", __name__)

def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@bp_shutdown.route("/shutdown")
def be_shutdown():
    shutdown_server()
    return "Server shutting down..."


def be_run():
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    print("***",this_path,"***")
    log_file = os.path.join(parent_path, "app.log")
    init_database()

    logging.basicConfig(filename=log_file, level=logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    auto_cancel_scheduler = BackgroundScheduler()
    global_scheduler.instance_GlobalAutoCancelOrder = global_scheduler.GlobalAutoCancelOrder(auto_cancel_scheduler)
    auto_cancel_scheduler.start()

    auto_return_scheduler = BackgroundScheduler()
    global_scheduler.instance_AutoAdmmitReturn = global_scheduler.GlobalAutoAdmmitReturn(auto_return_scheduler)
    auto_return_scheduler.start()

    app = Flask(__name__)
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    app.run()




