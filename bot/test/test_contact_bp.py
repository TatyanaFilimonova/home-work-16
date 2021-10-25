"""
Testing contact blueprint for flask app 'bot'
"""
#pylint: disable=W0614
#pylint: disable=W0611
#pylint: disable=W0613
#pylint: disable=W0602
#pylint: disable=W0612
#pylint: disable=W0401
#pylint: disable=C0413

import sys
import os
import unittest
import pytest
import faker

faker = faker.Faker()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append('../')
from init_bp import *


PARAM_LIST = []
empty_dict = {
            "Name": '',
            "Birthday": '',
            "Email": '',
            "Phone": '',
            "ZIP": '',
            "Country": '',
            "Region": '',
            "City": '',
            "Street": '',
            "House": '',
            "Apartment": ''
            }

TEST_EDIT_DICT = {
        "Name": 'John Snow jnr',
        "Birthday": '1900-10-10',
        "Email": 'snow@westeros.com',
        "Phone": '380506709090',
        "ZIP": '090',
        "Country": 'Westeros',
        "Region": '',
        "City": '',
        "Street": '',
        "House": '',
        "Apartment": ''
    }


def fill_param():
    """
    Create test datases
    :return:
    """
    global PARAM_LIST
    for i in range(1,10):
        test_dict = {
            "Name": faker.name(),
            "Birthday": faker.date(),
            "Email": faker.email(),
            "Phone": faker.msisdn(),
            "ZIP": faker.postcode(),
            "Country": faker.country(),
            "Region": '',
            "City": faker.city(),
            "Street": faker.street_name(),
            "House": faker.building_number(),
            "Apartment": faker.building_number()
            }
        PARAM_LIST.append(test_dict)

fill_param()


@pytest.mark.parametrize("data_dict", PARAM_LIST)
def test_contact_insert(app, client, data_dict):
    """
    Test /contact/add_contact handler for postgres
    :param app: fixture
    :param client: fixture
    :param data_dict: fixture
    :return:
    """
    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/add_contact', data=data_dict)
    assert b'Contact successfully saved' in response.data, 'is contact successfully saved'

    response = client.post('/contact/add_contact', data=data_dict)
    assert b'error' in response.data, 'duplicated records should be prohibited'

    #lets do some cleaning
    stmt = delete(Contact).where(Contact.name == data_dict['Name'])
    pgsession.execute(stmt)
    pgsession.commit()


@pytest.mark.parametrize("data_dict", PARAM_LIST)
def test_contact_insert_mongo(app, client, data_dict):
    """
    Test /contact/add_contact handler for mongo
    :param app: fixture
    :param client: fixture
    :param data_dict: fixture
    :return:
    """
    response = client.post('/DB_select', data={'db': 'mongodb'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/add_contact', data=data_dict)
    assert b'Contact successfully saved' in response.data, 'is contact successfully saved'

    response = client.post('/contact/add_contact', data=data_dict)
    assert b'error' in response.data, 'duplicated records should be prohibited'

    #lets do some cleaning
    contact_to_delete = contact_db.find_one(
        {'name': data_dict['Name'],
         'birthday': datetime.strptime(data_dict['Birthday'], '%Y-%m-%d')})
    if contact_to_delete:
        contact = ContactbookMongo(contact_db, counter_db)
        contact.delete_contact(contact_to_delete['contact_id'])

def test_empty_dict(app, client):
    """
        Test /contact/add_contact handler with empty client for postgres
        :param app: fixture
        :param client: fixture
        :return:
        """
    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/add_contact', data=empty_dict)
    assert b'Create new contact' in response.data


def test_edit_contact(app, client):
    """
    Test /contact/edit_contact handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """
    global TEST_EDIT_DICT

    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.get('/contact/edit_contact')
    assert response.status_code == 200
    assert b'Find a contact' in response.data

    response = client.post('/contact/edit_contact')
    assert response.status_code == 400

    response = client.post('/contact/edit_contact', data={'Keywords':'man'})
    assert b'Contacts by your request: click on ID to edit contact' in response.data


    response = client.post('/contact/add_contact', data=TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save test contact'

    contacts = ContactbookPSQL(pgsession)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    response = client.get(f'/contact/edit_contact/{contact[0].contact_id}')
    assert b'Please edit Contact details' in response.data

    TEST_EDIT_DICT["Name"] = 'John Snow snr'

    response = client.post(f'/contact/edit_contact/{contact[0].contact_id}', data = TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save edited test contact'

    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    contacts.delete_contact(contact[0].contact_id)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 0


def test_edit_contact_mongo(app, client):
    """
    Test /contact/edit_contact handler for mongo
    :param app: fixture
    :param client: fixture
    :return:
    """
    global TEST_EDIT_DICT

    response = client.post('/DB_select', data={'db': 'mongodb'})
    assert response.status_code == 302, 'database selected'

    response = client.get('/contact/edit_contact')
    assert response.status_code == 200
    assert b'Find a contact' in response.data

    response = client.post('/contact/add_contact', data=TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save test contact'

    contacts = ContactbookMongo(contact_db, counter_db)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    response = client.get(f'/contact/edit_contact/{contact[0].contact_id}')
    assert b'Please edit Contact details' in response.data

    TEST_EDIT_DICT["Name"] = 'John Snow snr'

    response = client.post(f'/contact/edit_contact/{contact[0].contact_id}', data = TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save edited test contact'

    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    contacts.delete_contact(contact[0].contact_id)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 0



def test_find_contact(app, client):
    """
    Test /contact/find_contact handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """

    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.get('/contact/find_contact')
    assert b'Input search string: name or phone or even a part of it' in response.data

    response = client.post('/contact/find_contact', data={'Keywords':'man'})
    assert b'Contacts by your request: click on ID to edit contact' in response.data

def test_show_all_contact(app, client):
    """
    Test /contact/show_all_contacts handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """

    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.get('/contact/show_all_contacts')
    assert b'All the contacts from your address book. Click ID to see details' in response.data

    response = client.post('/contact/show_all_contacts')
    assert response.status_code == 405

    response = client.get('/contact/show_all_contacts', data={'some': 'wrong'})
    assert b'All the contacts from your address book. Click ID to see details' in response.data


def test_show_all_contact_mongo(app, client):
    """
    Test /contact/show_all_contacts handler for mongo
    :param app: fixture
    :param client: fixture
    :return:
    """

    response = client.post('/DB_select', data={'db': 'mongodb'})
    assert response.status_code == 302, 'database selected'

    response = client.get('/contact/show_all_contacts')
    assert b'All the contacts from your address book. Click ID to see details' in response.data

    response = client.post('/contact/show_all_contacts')
    assert response.status_code == 405

    response = client.get('/contact/show_all_contacts', data={'some': 'wrong'})
    assert b'All the contacts from your address book. Click ID to see details' in response.data



def test_contact_detail(app, client):
    """
    Test /contact/add_contact handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """

    global TEST_EDIT_DICT

    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/add_contact', data=TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save test contact'

    contacts = ContactbookPSQL(pgsession)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    response = client.get(f'/contact/contact_detail/{contact[0].contact_id}')
    assert b'User details' in response.data

    response = client.post(f'/contact/contact_detail/{contact[0].contact_id}')
    assert b'User details' in response.data

    contacts.delete_contact(contact[0].contact_id)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 0

def test_next_birthday(app, client):
    """
    Test /contact/next_birthday handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """
    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/next_birthday', data={'Period' : '1'})
    assert b'Contacts with Birthday at the nearest' in response.data

    response = client.post('/contact/next_birthday', data={'Period' : '-10'})
    assert b'You could use numbers only, the period should be' in response.data

    response = client.post('/contact/next_birthday', data={'Period' : 'asdasdasd'})
    assert b'You could use numbers only, the period should be' in response.data


def test_next_birthday_mongo(app, client):
    """
    Test /contact/next_birthday handler for mongo
    :param app: fixture
    :param client: fixture
    :return:
    """
    response = client.post('/DB_select', data={'db': 'mongodb'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/next_birthday', data={'Period' : '1'})
    assert b'Contacts with Birthday at the nearest' in response.data

    response = client.post('/contact/next_birthday', data={'Period' : '-10'})
    assert b'You could use numbers only, the period should be' in response.data

    response = client.post('/contact/next_birthday', data={'Period' : 'asdasdasd'})
    assert b'You could use numbers only, the period should be' in response.data


def test_delete_contact(app, client):
    """
    Test /contact/delete_contact handler for postgres
    :param app: fixture
    :param client: fixture
    :return:
    """
    response = client.get('/contact/delete_contact')
    assert response.status_code == 200
    assert b'Select contact to delete' in response.data

    response = client.post('/contact/delete_contact', data={'Keywords' : 'man'})
    assert response.status_code == 200
    assert b'Found contacts to delete' in response.data

    response = client.post('/contact/delete_contact', data={'wrong': 'man'})
    assert response.status_code == 400

    global TEST_EDIT_DICT

    response = client.post('/DB_select', data={'db': 'postgres'})
    assert response.status_code == 302, 'database selected'

    response = client.post('/contact/add_contact', data=TEST_EDIT_DICT)
    assert b'Contact successfully saved' in response.data, 'save test contact'

    contacts = ContactbookPSQL(pgsession)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 1

    response = client.get(f'/contact/delete_contact/{contact[0].contact_id}')
    assert b'succesfully deleted' in response.data

    contacts = ContactbookPSQL(pgsession)
    contact = contacts.get_contacts(TEST_EDIT_DICT['Name'])
    assert len(contact) == 0

    response = client.get(f'/contact/delete_contact/{"0&&&&&&&"}')
    assert b'error' in response.data

    response = client.get(f'/contact/delete_contact/{"asdasdasd"}')
    assert b'error' in response.data

    response = client.get(f'/contact/delete_contact/{100000000000000000100000000000}')
    assert b'error' in response.data
