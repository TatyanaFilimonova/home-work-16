# pylint: disable=W0614
# pylint: disable=W0401
# pylint: disable=E0402
# pylint: disable=C0413

"""
Blueprint init for Flask application Bot
"""

# local packages
import sys
import os
import warnings
from flask import redirect, url_for, session, render_template, request


warnings.filterwarnings("ignore")


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
if __package__ == "" or __package__ is None:
    from neural_code import *
    from LRU_cache import *
    from db_mongo import contact_db, counter_db, note_db, user_db, db
    from db_postgres import pgsession
    from users_data_classes import *
    from note_bp import *
    from notes_data_classes import *
    import global_var
else:
    from .neural_code import *
    from .LRU_cache import *
    from .db_mongo import contact_db, counter_db, note_db, user_db, db
    from .db_postgres import pgsession
    from .users_data_classes import *
    from .note_bp import *
    from .notes_data_classes import *
    from . import global_var

# global packages


init_bp = Blueprint("init", __name__, url_prefix="")
command_history = {"command": "response"}


# routes section


# Check session for db is initialized and user  is logined
def before_request():
    """
    DB choose implementation
    Session used to store DB status and current user info
    :return:
    """
    if "db" not in session or global_var.contact_book is None:
        if request.endpoint not in ["init.db_select", "db_select"]:
            return redirect(url_for("init.db_select"))
        return None
    if ("user" not in session or session["user"] is None) and request.endpoint not in [
        "login.login",
        "login.register",
    ]:
        return redirect(url_for("login.login"))
    return None


@init_bp.route("/hello_", methods=["GET", "POST"])
def hello_():
    """
    Greetengs from the bot in the command history and redirect to main form
    :return: rendered HTML
    """
    return redirect("/bot-command")


@init_bp.route("/help_", methods=["GET", "POST"])
def help_():
    """
    Info about available bot features
    :return: rendered HTML
    """
    return render_template("help/help.html", exec_command=exec_command)


@init_bp.route("/")
def index():
    """
    Just  redirection from root route to bot
    """

    return redirect(url_for("init.bot"))


@init_bp.route("/DB_select", methods=["GET", "POST"])
def db_select():
    """
    Before request middleware
    Prepare BD and redirect to login user
    GET - prepare a form to select DB
    POST - set the DB and redirect user to login
    :return: rendered HTML
    """
    if request.method == "POST":
        option = request.form["db"]
        flush_cache()
        session["user"] = None
        session["db"] = None
        if option == "mongodb":
            global_var.contact_book = ContactbookMongo(contact_db, counter_db)
            global_var.note_book = NotebookMongo(note_db, counter_db)
            global_var.users_db = AppUserMongo(user_db)
            session["db"] = "choosed"
        else:
            global_var.contact_book = ContactbookPSQL(pgsession)
            global_var.note_book = NotebookPSQL(pgsession)
            global_var.users_db = AppUserPSQL(pgsession)
            session["db"] = "choosed"
        return redirect(url_for("login.login"))
    return render_template("select_db.html")


@init_bp.route("/bot-command", methods=["GET", "POST"])
def bot():
    """
    web form for communication between bot and user
    GET - render the form
    POST - handle user intentions
    :return: rendered HTML
    """
    if request.method == "POST":
        command = request.form.get("BOT command")
        neural_response = listener(command)
        command_history[command] = neural_response["description"]
        return redirect(url_for(exec_command[neural_response["to_call"]][0]))
    return render_template("bot_page.html", command_history=command_history)


# end of routes section


exec_command = {
    "hello": ["init.hello_", "hello:  Greetings"],
    "add contact": ["contact.add_contact", "add contact: Add a new contact"],
    "edit contact": [
        "contact.edit_contact",
        "edit contact: Edit the contact detail",
    ],
    "find contact": [
        "contact.find_contact",
        "find contact: Find the records by phone or name",
    ],
    "find notes": ["note.find_notes", "find notes: Find the notes by text or keywords"],
    "show all contacts": [
        "contact.show_all_contacts",
        "show all contacts: Print all the records of address book",
    ],
    "show all notes": [
        "note.show_all_notes",
        "show all_notes: Print all the records of address book ",
    ],
    "help": ["init.help_", "help: Print a list of the available commands"],
    "add note": ["note.add_note", "add note: Add new text note "],
    "edit note": ["note.edit_note", "edit note: Edit existing text note "],
    "delete contact": ["contact.delete_contact", "delete contact: Delete contact"],
    "delete note": ["note.delete_note", "delete note: Delete text note"],
    "next birthday": [
        "contact.next_birthday",
        "next birthday: Let you the contacts with birthdays in specified period",
    ],
    "logout": ["login.logout", "user logout: change active user"],
    "choose data engine": ["init.db_select", "Change current database engine"],
}


@LRU_cache(max_len=10)
def listener(message):
    """
    Define user intention using neural predictions
    :param message: str
    :return: res : dict
    """
    return_list, intent_dict = predict_class(message)
    if not return_list:
        return {"description": "Hello!", "to_call": "help"}
    res = get_response(return_list, intent_dict)
    return res


def close_db():
    """Closes db  connection"""
    pgsession.close()
    db.close()
    session.clear()
    print("Databases are closed")
