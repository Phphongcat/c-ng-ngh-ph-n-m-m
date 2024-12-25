# Wellcome to my flask python web project

## if use want test online, use [the url](https://phphongcat.pythonanywhere.com/)

## THIS IS STEP OF SETUP AND RUN APP IN LOCAL
### First, this is how to setup mysql server
  - using cnpm.sql file to adding your new database.
  - open file \__init__.app at `app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/cnpm?charset=utf8mb4' % quote('xxxxxxx')`
  - edit the name `root` to name of database account
  - edit the name `xxxxxxx` to password of database account
  - edit the name `cnpm` to name of your new database

### Second, this is how to run the web
- open the terminal and type `.venv\Scripts\activate` then enter
- continue type `pip install -r requirements.txt` then enter
- after all, run index.py file to run the web project.
- double click [http://127.0.0.1:5000](http://127.0.0.1:5000) to show the web

## THIS IS DETAIL WEB
### flask-admin
- using `http://127.0.0.1:5000/admin` to direct admin page
- login with account: admin, password: 123
- click to `room`, `cateory` or `pricing` to seeing database
- you can edit these databases
- you can see `stats` to view stats with chartjs
- finally, you can register SALE account in `register` tab

### APScheduler
- the web using APScheduler to set active ticket expired
- the APScheduler will invoke this function every 1 minute

### sms
- you can receive sms when you reversation success a ticket

### SQLalchemy
- the web using sqlalchemy to make relationship and model of database

### InvoicePDF
- the web using InvoicePDF to make invoke file of payment

Thanks for seeing <3.
