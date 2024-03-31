from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature



app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentobike.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SECURITY_PASSWORD_SALT'] = 'your_security_password_salt'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    pincode = db.Column(db.String(20), nullable=True)
    mobile_number = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)

class Bicycle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    bike_type = db.Column(db.String(50), nullable=True)
    # Add more fields as necessary, such as image URLs

    owner = db.relationship('User', backref=db.backref('bicycles', lazy=True))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    bicycle_id = db.Column(db.Integer, db.ForeignKey('bicycle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # Example statuses: pending, confirmed, cancelled
    bicycle = db.relationship('Bicycle', backref=db.backref('bookings', lazy=True))
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    bicycle_id = db.Column(db.Integer, db.ForeignKey('bicycle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    bicycle = db.relationship('Bicycle', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))

with app.app_context():
    db.create_all()

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except (SignatureExpired, BadSignature):
        return False
    return email

@app.route('/')
def home():
    bicycles = Bicycle.query.order_by(Bicycle.id.desc()).limit(4).all()
    username = session.get('username')
    return render_template('home.html', username=username, bicycles=bicycles)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        user_type = request.form.get('user_type')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        mobile_number = request.form.get('mobile_number')
        city = request.form.get('city')
        country = request.form.get('country')
        terms_accepted = 'terms_accepted' in request.form  # Check if terms_accepted checkbox is checked

        if not terms_accepted:
            flash("You must agree to the terms and conditions to sign up.", "error")
            return redirect(url_for('signup'))

        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            flash("User already exists!", "error")  # Using flash to show error message
            return redirect(url_for('signup'))

        # Create a new User instance including the new fields
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            user_type=user_type,
            address=address,
            pincode=pincode,
            mobile_number=mobile_number,
            city=city,
            country=country
        )


        db.session.add(new_user)
        db.session.commit()

        # Automatically log the user in
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['user_type'] = new_user.user_type

        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type

            return redirect(url_for('home'))
        else:
            return "Invalid username or password", 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    # Remove user from session to log them out
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/add-bicycle', methods=['GET', 'POST'])
def add_bicycle():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        bike_type = request.form.get('bike_type')
        owner_id = session.get('user_id')

        # Ensure the upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        photo_urls = []
        if 'bicyclePhotos' in request.files:
            photo_files = request.files.getlist('bicyclePhotos')
            for photo in photo_files:
                if photo and photo.filename:
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(photo.filename)}"
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    photo.save(photo_path)
                    # Store the relative path from the static directory
                    photo_urls.append(os.path.join('uploads', unique_filename))

        # Here you would need to adjust how you handle multiple image URLs based on your database schema
        image_url = ';'.join(photo_urls)  # Example: joining URLs by semicolon as a simple solution

        new_bicycle = Bicycle(name=name, description=description, bike_type=bike_type, owner_id=owner_id, image_url=image_url)
        db.session.add(new_bicycle)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('add_bicycle.html')


@app.route('/bicycle_details/<int:bicycle_id>')
def bicycle_details(bicycle_id):
    bicycle = Bicycle.query.get_or_404(bicycle_id)
    # Splitting the image URLs into a list if image_url is not None
    if bicycle.image_url:
        bicycle.image_urls = bicycle.image_url.split(';')
    else:
        bicycle.image_urls = []
    return render_template('bicycle_details.html', bicycle=bicycle)



@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    return render_template('user_profile.html', user=user)


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/book-bicycle/<int:bicycle_id>', methods=['GET', 'POST'])
def book_bicycle(bicycle_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    bicycle = Bicycle.query.get_or_404(bicycle_id)

    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']

        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        new_booking = Booking(
            user_id=session['user_id'],
            bicycle_id=bicycle_id,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('booking_confirmation', booking_id=new_booking.id))

    return render_template('book_bicycle.html', bicycle=bicycle)



@app.route('/submit_review/<int:bicycle_id>', methods=['POST'])
def submit_review(bicycle_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    rating = request.form.get('rating')
    comment = request.form.get('comment')
    user_id = session['user_id']

    review = Review(rating=rating, comment=comment, bicycle_id=bicycle_id, user_id=user_id)
    db.session.add(review)
    db.session.commit()

    return redirect(url_for('bicycle_details', bicycle_id=bicycle_id))


@app.route('/bicycles')
def bicycles():
    page = request.args.get('page', 1, type=int)  # Default to first page
    per_page = 10  # Number of items per page

    # Fetch the paginated bicycles
    pagination = Bicycle.query.paginate(page=page, per_page=per_page, error_out=False)
    bicycles = pagination.items

    return render_template('bicycles.html', bicycles=bicycles, pagination=pagination)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/bicycle/<int:bicycle_id>')
def bicycle_detail(bicycle_id):
    bicycle = Bicycle.query.get_or_404(bicycle_id)
    return render_template('bicycle_details.html', bicycle=bicycle)

@app.route('/booking-confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    bicycle = booking.bicycle  # Access the bicycle related to the booking
    owner = User.query.get(bicycle.owner_id)  # Access the owner of the bicycle

    if not owner.address or not owner.city or not owner.mobile_number:
        print("Missing owner information for user ID:", owner.id)
    return render_template('booking_confirmation.html', booking=booking, bicycle=bicycle, owner=owner)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        mobile_number = request.form.get('mobile_number')

        return redirect(url_for('reset_password'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('reset_password'))

        user_id = session.get('user_id')
        if user_id:

            user = User.query.get(user_id)

            user.password = generate_password_hash(password)

            db.session.commit()

            flash('Password reset successfully. Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid user. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('reset_password.html')


if __name__ == '__main__':
    app.run(debug=True)
