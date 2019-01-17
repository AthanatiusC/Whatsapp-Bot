from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime, time, csv, sys
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import Column, String, TIMESTAMP, Text, Time, Date, Integer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
login = LoginManager()
login.init_app(app)


app.secret_key = "Flash"
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:''@localhost:3306/wbs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

base_url = "http://localhost:8081/"
date_now = datetime.datetime.today().strftime('%Y-%m-%d')
time_now = datetime.datetime.now().strftime("%H:%M:%S")

db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column('id', primary_key=1)
    name = Column('name', String(50))
    username = Column('username', String(50))
    password = Column('password', String(255))
    email = Column('email', String(255))
    picture = Column('picture', String(255))
    registered_at = Column('registered_at', Date())

    def __init__(self, name, username, password, email, picture, registered_at):
        self.id = id
        self.name = name
        self.username = username
        self.password = password
        self.email = email
        self.picture = picture
        self.registered_at = registered_at

class Groups(db.Model):
    __tablename__ = "Groups"
    id = Column("id", primary_key=1)
    group_name = Column('group_name', String(32))
    link = Column('link', String(32))
    date_added = Column('date_added', TIMESTAMP)

    def __init__(self, group_name, link, date_added):
        self.id = id
        self.group_name = group_name
        self.link = link
        self.date_added = date_added

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class Joined_groups(db.Model):
    __tablename__ = "joined_groups"
    id = Column("id", primary_key=1)
    group_name = Column('group_name', String(255))
    user = Column('user', String(100))
    date_added = Column('date_added', TIMESTAMP)

    def __init__(self, group_name, user, date_added):
        self.id = id
        self.group_name = group_name
        self.user = user
        self.date_added = date_added

class Contacts(db.Model):
    __tablename__ = "contacts"
    id = Column("id", primary_key=1)
    phone = Column("phone", String(15))
    name = Column("name", String(100))
    date_added = Column("date_added", TIMESTAMP)

    def __init__(self, phone, name, date_added):
        self.id = id
        self.phone = phone
        self.name = name
        self.date_added = date_added


class Messages(db.Model):
    __tablename__ = "messages"
    id = Column("id", primary_key=1)
    sender = Column('sender', String(14))
    receiver = Column('sender', String(14))
    msg = Column('msg', Text())
    date = Column('date', Date())
    time = Column('date', Time())

    def __init__(self, sender, receiver, msg, date, time):
        self.id = id
        self.sender = sender
        self.receiver = receiver
        self.msg = msg
        self.date = date
        self.time = time

def waitForLogged():
    i = 0



@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))

@app.route('/index')
@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=["POST","GET"])
def login():
    if request.method == "POST":
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username, password=password).first()

            if user is None:
                flash("Invalid credentials", 'danger')
                return redirect(url_for('login'))
            else:
                login_user(user)
                return redirect(url_for('index'))


    else:
        if current_user.is_authenticated:
            return redirect('/')
        else:
            return render_template('pages/users/login.html')

@app.route('/register', methods=["POST","GET"])
def register():
    if request.method == "POST":
        fullname = request.form['name']
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']

        regs = User(name=fullname,username=username,password=password,email=email,picture='default.png',registered_at=date_now)
        db.session.add(regs)
        db.session.commit()

        flash("Success register! Now you can login", "success")
        return redirect(url_for('login'))
    else:
        return render_template('pages/users/register.html')

@app.route('/logged')
@login_required
def logged():
    return "Hello, "+current_user.email

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    data_user = User.query.filter_by(id=current_user.id)
    return render_template('pages/users/settings.html', data=data_user)


@app.route('/messages')
def messages():
    message_list = Messages.query.all()
    return render_template('pages/messages/messages.html', messages= message_list)


@app.route('/messages/add', methods=["POST","GET"])
def add_messages():
    if request.method == "GET":
        return render_template('pages/messages/add_messages.html')
    else:
        type = request.form["type"]
        target = request.form["target"]
        msg = request.form['msg']

        driver = webdriver.Chrome()
        if type == "single":
            driver.get('https://web.whatsapp.com/send?phone=' + target + '&text=' + msg)
            time.sleep(10)
            logged = False
            while not logged:
                try:
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_3dqpi")))
                    logged = True
                except ValueError:
                    logged = False

            text = driver.find_element_by_class_name('_2S1VP')
            text.send_keys(msg)

            time.sleep(1)
            element = driver.find_element_by_class_name('_35EW6')
            element.click()

            messages = Messages("081380353611", target, msg, date_now, time_now)
            db.session.add(messages)
            db.session.commit()

            driver.close()

            flash('Message sent!', 'success')
            return redirect(url_for('messages'))
        elif type == "all":
            all_contacts = Contacts.query.all()
            for contacts in all_contacts:
                driver.get('https://web.whatsapp.com/send?phone=' + contacts.phone + '&text=' + msg)
                time.sleep(10)

                logged = False
                while not logged:
                    try:
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_3dqpi")))
                        logged = True
                    except ValueError:
                        logged = False

                text = driver.find_element_by_class_name('_2S1VP')
                text.send_keys(msg)

                time.sleep(1)
                element = driver.find_element_by_class_name('_35EW6')
                element.click()

                messages = Messages("081380353611", target, msg, date_now, time_now)
                db.session.add(messages)
                db.session.commit()

                time.sleep(1)
            driver.close()
            flash("Success send messages to all contacts!", "success")
            return redirect("messages/add")
        else:
            joined_group = Joined_groups.query.all()

            driver.get("https://web.whatsapp.com/")
            i = 0
            while i == 0:
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "_2wP_Y"))
                    )
                    i = 1
                except:
                    i = 0
            groups_name = []
            for join_group in joined_group:
                groups_name.append(join_group)

            for group_name in groups_name:
                searchbox = driver.find_element_by_class_name("jN-F5")

                time.sleep(1)

                searchbox.send_keys(group_name)
                searchbox.send_keys(Keys.ENTER)

                time.sleep(5)


@app.route('/contacts', methods=["GET","POST"])
def contacts():
    if request.method == "GET":
        delete = request.args.get('delete')
        if delete:
            Contacts.query.filter_by(id=delete).delete()
            db.session.commit()

            flash("Success delete contact", 'success')
            return redirect("contacts")
        else:
            contacts_list = Contacts.query.limit(5)
            return render_template('pages/contacts/contacts.html', contacts=contacts_list)



    else:
        file = request.files['contacts']
        file.save("static/files/csv/"+file.filename)

        csv_url = base_url+"static/files/csv/"+file.filename
        with open("static/files/csv/"+file.filename) as csv_file:
            readcsv = csv.reader(csv_file, delimiter=",")
            name = []
            listNo = []
            for row in readcsv:
                listNo.append(row[1])
                name.append(row[0])

            num = 0
            while num <= len(listNo):
                nomor = listNo[num]
                nama = name[num]
                contact = Contacts(phone=nomor, name=nama, date_added=date_now)
                db.session.add(contact)
                db.session.commit()

                num += 1

            flash("Success import contacts", "success")
            return redirect(url_for('contacts'))


@app.route('/contacts/add', methods=["POST","GET"])
def add_contacts():
    if request.method == "POST":
        return "POSTED"
    else:
        return render_template('pages/contacts/add_contacts.html')


@app.route('/groups')
def groups():
    grup = Groups.query.all()
    return render_template('pages/groups/groups.html', grup=grup)

@app.route('/groups/joined_groups', methods=['GET', 'POST'])
def Joined():
    if request.method == "GET":
        delete = request.args.get('delete')

        if delete:
            Joined_groups.query.filter_by(id=delete).delete()
            db.session.commit()

            flash('Success delete joined groups', 'success')
            return redirect('groups/joined_groups')
        else:
            joined_groups_all = Joined_groups.query.all()
            return render_template('pages/groups/joined_groups.html', data=joined_groups_all)
    else:
        group_name = request.form['name']

        logged_user = current_user.username
        G = Joined_groups(group_name, logged_user, date_now)

        db.session.add(G)
        db.session.commit()

        flash('Success add joined group!', 'success')
        return redirect(url_for('groups')+'/joined_groups')



@app.route('/groups/joined_groups/import')
def import_groups():
    driver = webdriver.Chrome()
    driver.get('https://web.whatsapp.com/')

    i=0
    while i == 0:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "_2wP_Y"))
            )
            i = 1
        except:
            i = 0
    time.sleep(5)
    list_all = driver.find_elements_by_css_selector("._1wjpf:not(._3NFp9)")
    time.sleep(2)

    list_name = []
    for list in list_all:
        list_name.append(list.text)

    for list_group in list_name:
        staleElement = False
        while staleElement == False:
            try:
                app.logger.warning(list_group)
                staleElement = True
            except:
                staleElement = False
                return "Please reload to try again"

        searchbox = driver.find_element_by_class_name("jN-F5")

        time.sleep(1)

        searchbox.send_keys(list_group)
        searchbox.send_keys(Keys.ENTER)

        time.sleep(5)

        # Click the burget btn
        burger_btn = driver.find_element_by_css_selector('._1i0-u [title=Menu]')
        burger_btn.click()

        # Check is this a group or not

        try:
            info = driver.find_element_by_css_selector('[title="Group info"]')
            driver.implicitly_wait(10)

            J = Joined_groups(list_group, current_user.username, date_now)
            db.session.add(J)
            db.session.commit()
        except:
            continue








    flash('Success add groups', 'success')
    return redirect(url_for('groups')+'/joined_groups')





@app.route('/groups/add', methods=["POST","GET"])
def add_groups():
    if request.method == "GET":
        return render_template('pages/groups/add_groups.html')
    else:
        if 'manual' in request.form:
            group_name = request.form['name']
            link = request.form['link']

            G = Groups(group_name=group_name, link=link, date_added=date_now)
            db.session.add(G)
            db.session.commit()

            flash("Success add group!", "success")
            return redirect(url_for("groups"))

        elif 'scrape' in request.form:
            keyword = request.form['keyword']

            driver = webdriver.Chrome()
            driver.get(
                "http://ngarang.com/link-grup-wa/daftar-link-grup-wa.php?search={}&searchby=name".format(keyword))
            driver.implicitly_wait(2)
            num = 1

            titles = driver.find_elements_by_class_name("wa-chat-title-text")
            links = driver.find_elements_by_css_selector(".URLMessage")
            listLinks = []
            listTitle = []

            for link in links:
                listLinks.append(link.text)

            for title in titles:
                listTitle.append(title.text)

            list = 0
            while list <= 23:
                G = Groups(group_name=listTitle[list], link=listLinks[list], date_added=date_now)
                db.session.add(G)
                db.session.commit()
                list += 1
            driver.close()
            flash("Success grab all groups with keyword "+keyword, "success")
            return redirect("groups")
        elif 'manual' in request.form:
            return "MANUAL"
        else:
            return "NOTHING"

@app.route('/groups/join', methods=["GET"])
def join_group():
    group_links = Groups.query.all()
    driver = webdriver.Chrome()
    for group_link in group_links:
        driver.get(group_link.link)
        driver.implicitly_wait(5)

        btn = driver.find_element_by_id('action-button')
        btn.click()


        WebDriverWait(driver, 10).until( EC.element_to_be_clickable((By.CLASS_NAME, "PNlAR")))

        btn_join = driver.find_element_by_class_name("PNlAR")
        btn_join.click()

    flash('Success join all group!', 'success')
    return redirect(url_for('groups'))




if __name__ == "__main__":
    app.run(debug=True, port=8081)
