#Wellcome to my flask python web project

##if use want test online, use [the url](https://phphongcat.pythonanywhere.com/)

##THIS IS STEP OF SETUP AND RUN APP IN LOCAL:
###First, this is how to setup mysql server and run web:
1. using cnpm.sql file to adding your new database.
2. open file \__init__.app\ at app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/cnpm?charset=utf8mb4' % quote('xxxxxxx')
3. edit the name 'root' to name of database account
4. edit the name 'xxxxxxx' to password of database account
5. edit the name 'cnpm' to name of your new database
6. run index.py file to run the web project.
7. double click [http://127.0.0.1:5000](http://127.0.0.1:5000) to show the web

###
