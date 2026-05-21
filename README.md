# Lightseed Solutions LLP — Full-Stack Website

## Tech Stack
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, JavaScript (ES6+)
- **Backend**: Python 3 / Flask
- **Database**: SQLite (via Python built-in sqlite3)
- **Icons**: Bootstrap Icons
- **Fonts**: Cormorant Garamond + DM Sans (Google Fonts)
- **Images**: Unsplash (free, no auth required)

## Project Structure
```
lightseed/
├── app.py                  # Flask application & all routes
├── requirements.txt
├── README.md
├── instance/
│   └── lightseed.db        # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── lightseed.css   # All custom styles + Bootstrap overrides
│   ├── js/
│   │   └── main.js         # Scroll animations, form handling, counters
│   └── images/
│       └── logo.jpg        # Lightseed brand logo
└── templates/
    ├── base.html           # Base layout (navbar, footer, WhatsApp, ticker)
    ├── index.html          # Home page
    ├── about.html          # About Us + Founder + Team
    ├── services.html       # All programs overview
    ├── healing.html        # Healing & Inner Alignment
    ├── training.html       # Leadership & Behavioural Training
    ├── therapy.html        # Therapy & Coaching
    ├── shuddhi.html        # Lightseed Shuddhi (POSH/POCSO/DEI)
    ├── education.html      # Education & Employability
    ├── testimonials.html   # Testimonials page
    ├── contact.html        # Contact + Enquiry Form
    └── admin/
        ├── login.html      # Admin login
        ├── base_admin.html # Admin layout with sidebar
        ├── dashboard.html  # Stats, recent enquiries, page views
        ├── enquiries.html  # Manage & update enquiry status
        ├── testimonials.html # Approve/delete testimonials
        ├── programs.html   # Add/toggle programs
        └── newsletter.html # View & export subscribers

## Setup & Run

### 1. Install dependencies
```bash
pip install flask
# or: pip install -r requirements.txt
```

### 2. Run the development server
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000        # Website
http://localhost:5000/admin  # Admin panel
```

### Admin Credentials (default)
- **Username**: admin
- **Password**: lightseed2025

> Change these in app.py → `init_db()` before deploying to production.

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/enquiry` | Submit contact form |
| POST | `/api/newsletter` | Subscribe to newsletter |
| GET | `/api/programs` | List all active programs |
| GET | `/api/programs?category=healing` | Filter by category |
| GET | `/api/testimonials` | List approved testimonials |
| GET | `/api/stats` | Site statistics |

## Pages
| URL | Page |
|-----|------|
| `/` | Home |
| `/about` | About Us |
| `/services` | All Programs |
| `/healing` | Healing & Wellbeing |
| `/training` | Leadership Training |
| `/therapy` | Therapy & Coaching |
| `/shuddhi` | Lightseed Shuddhi |
| `/education` | Education Programs |
| `/testimonials` | Testimonials |
| `/contact` | Contact Us |
| `/admin` | Admin Dashboard |

## Responsive Design
- Bootstrap 5 grid (xs → xl breakpoints)
- Mobile-first approach
- Hamburger nav on mobile
- Stacked layouts on small screens
- Touch-friendly card interactions

## Features
- ✅ Animated Lightseed logo in navbar
- ✅ Floating WhatsApp button (+91 9988154353)
- ✅ Scroll progress bar (gold → teal gradient)
- ✅ Infinite marquee ticker
- ✅ 8 scroll animation types (fade-up, blur-in, flip-in, etc.)
- ✅ Card tilt on hover (3D perspective)
- ✅ Auto-stagger animation for grid children
- ✅ Counter animations (page views, stats)
- ✅ Page-specific colour moods (blue=training, yellow=healing, lavender=therapy)
- ✅ Social feed switcher (Instagram/YouTube/LinkedIn)
- ✅ Contact form → stored in SQLite
- ✅ Newsletter subscription
- ✅ Full admin panel with CRM
- ✅ Enquiry status management (New → Contacted → Converted → Closed)
- ✅ Testimonial approval workflow
- ✅ Program management (add/activate/deactivate)
- ✅ Newsletter subscriber export (CSV)
- ✅ Page view tracking

## Production Deployment
For production, replace the development server with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Set a strong SECRET_KEY environment variable:
```bash
export SECRET_KEY="your-very-secret-key-here"
```

## Customisation
- **WhatsApp number**: Search `9988154353` in app.py and base.html
- **Email**: Search `mini@lightseed.in`
- **Founder photo**: Replace the Unsplash URL in about.html and index.html
- **Logo**: Replace `static/images/logo.jpg`
- **Admin password**: Change the default in `init_db()` in app.py
