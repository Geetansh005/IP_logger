# IP_logger
# 📍 Visitor Tracker

A Flask-based visitor tracking and location visualization project that demonstrates how a web application can collect visitor metadata, obtain browser-based geolocation with user permission, fall back to IP-based geolocation, store visitor records in SQLite, and visualize collected locations through an interactive dashboard.

> **⚠️ Privacy & Ethical Use**
>
> This project handles sensitive visitor information such as IP addresses, approximate/precise geographic coordinates, ISP information, browser/platform details, and timestamps.
>
> Use it only for authorized testing, security research, demonstrations, or applications where visitors have been properly informed and have provided the required consent. Do not use it to secretly track or identify people.

---

## ✨ Features

* 🌐 Flask web server
* 📍 Browser Geolocation API support
* 🎯 High-accuracy GPS collection when the browser permits it
* 🌎 IP-based geolocation fallback
* 🏙️ City, region, country and ISP information
* 🌐 Browser and operating-system detection
* 💾 SQLite database storage
* 📊 Visitor statistics dashboard
* 🗺️ Interactive Leaflet map
* 🔗 Tracking-link generation
* ↪️ Redirect to a supplied destination URL
* 🗑️ Delete individual visitor records
* 🔌 JSON API for visitor data
* 🔐 HTTPS support using SSL certificates
* 📱 Mobile-friendly frontend
* 🎨 Custom dark dashboard UI
* ⚡ No separate frontend framework required

---

# 🛠️ Tech Stack

## Backend

| Technology   | Purpose                                    |
| ------------ | ------------------------------------------ |
| **Python**   | Main programming language                  |
| **Flask**    | Web framework and routing                  |
| **SQLite**   | Local database                             |
| **Werkzeug** | Flask's underlying WSGI utilities          |
| **urllib**   | External HTTP requests                     |
| **JSON**     | Data exchange between frontend and backend |
| **SSL**      | HTTPS server support                       |
| **Socket**   | Detecting local LAN IP                     |

The application initializes Flask and stores the SQLite database alongside the Python application.

## Frontend

| Technology                  | Purpose                        |
| --------------------------- | ------------------------------ |
| **HTML5**                   | Page structure                 |
| **CSS3**                    | Styling and animations         |
| **JavaScript**              | Client-side functionality      |
| **Browser Geolocation API** | GPS/location acquisition       |
| **Fetch API**               | Sending location data to Flask |
| **Leaflet.js**              | Interactive maps               |
| **Google Maps URLs**        | Opening individual coordinates |
| **Google Fonts**            | Inter/Nunito typography        |

The dashboard loads Leaflet 1.9.4 and uses OpenStreetMap/CARTO map tiles.

## External Services

### IP Geolocation

The application uses an IP geolocation service to obtain:

* Public IP
* City
* Region
* Country
* ISP
* Latitude
* Longitude

The implementation queries `ip-api.com` and extracts the required geographic fields.

### Reverse Geocoding

GPS coordinates can be converted into human-readable location information using the Nominatim/OpenStreetMap reverse-geocoding endpoint.

---

# 📁 Project Structure

A typical project directory looks like:

```text
visitor-tracker/
│
├── dot.py
├── visitor_data.db
├── cert.pem
├── key.pem
├── README.md
│
└── .gitignore
```

### `dot.py`

Main application file containing:

* Flask configuration
* Database functions
* IP geolocation
* User-agent parsing
* Application routes
* HTML templates
* CSS
* JavaScript
* Dashboard
* HTTPS server startup

### `visitor_data.db`

SQLite database containing the collected visitor records.

### `cert.pem`

SSL/TLS certificate used to enable HTTPS.

### `key.pem`

Private SSL/TLS key used with the certificate.

> **Never commit `key.pem` to GitHub or expose it publicly.**

---

# 🗄️ Database Design

The application creates a SQLite table named `visitors`.

```sql
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT,
    latitude REAL,
    longitude REAL,
    accuracy_meters REAL,
    city TEXT,
    region TEXT,
    country TEXT,
    isp TEXT,
    location_source TEXT,
    user_agent TEXT,
    browser TEXT,
    platform TEXT,
    redirect_url TEXT,
    timestamp TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

The database is initialized automatically when the application starts.

## Stored Information

| Field             | Description                 |
| ----------------- | --------------------------- |
| `id`              | Unique visitor record ID    |
| `ip_address`      | Visitor IP address          |
| `latitude`        | Geographic latitude         |
| `longitude`       | Geographic longitude        |
| `accuracy_meters` | Browser GPS accuracy        |
| `city`            | City/town                   |
| `region`          | State/region                |
| `country`         | Country                     |
| `isp`             | Internet service provider   |
| `location_source` | `gps` or `ip`               |
| `user_agent`      | Browser user-agent string   |
| `browser`         | Detected browser            |
| `platform`        | Detected operating system   |
| `redirect_url`    | Destination URL             |
| `timestamp`       | Visit timestamp             |
| `created_at`      | Database creation timestamp |

---

# 🔄 How the Application Works

The application follows this general pipeline:

```text
                    ┌───────────────────┐
                    │      Visitor      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Tracking URL      │
                    │ /click?url=...    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Flask Server      │
                    │ /click            │
                    └─────────┬─────────┘
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
        ┌──────────────────┐    ┌──────────────────┐
        │ IP Geolocation   │    │ Browser          │
        │                  │    │ Geolocation API  │
        └────────┬─────────┘    └────────┬─────────┘
                 │                       │
                 │                       ▼
                 │              ┌─────────────────┐
                 │              │ GPS Coordinates │
                 │              └────────┬────────┘
                 │                       │
                 └───────────┬───────────┘
                             ▼
                   ┌────────────────────┐
                   │ /log_location      │
                   │ POST endpoint      │
                   └──────────┬─────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │ SQLite Database    │
                   │ visitor_data.db    │
                   └──────────┬─────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │ Dashboard          │
                   │ /dashboard         │
                   └──────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ┌───────────┐       ┌───────────┐
              │ Data Table │       │ Leaflet   │
              │            │       │ Map       │
              └───────────┘       └───────────┘
```

---

# 1️⃣ Application Startup

When `dot.py` is executed, Flask starts the application.

Before starting the web server, the application calls:

```python
init_db()
```

This creates the `visitors` table if it doesn't already exist.

The application then searches for:

```text
cert.pem
key.pem
```

If both files exist, an SSL context is created and the application starts over HTTPS on port `5000`.

---

# 2️⃣ Home Page

The `/` route displays the main Visitor Tracker interface.

Available actions include:

```text
Generate Tracking Link
View Dashboard
Track My Visit
```

The homepage is implemented directly inside the Flask application using `render_template_string()`.

---

# 3️⃣ Tracking Link Generation

The `/generate` route displays the tracking-link generator.

The user provides a destination URL such as:

```text
https://example.com
```

JavaScript validates that the URL begins with:

```text
http://
```

or:

```text
https://
```

It then creates a URL similar to:

```text
https://your-server.com/click?url=https%3A%2F%2Fexample.com
```

The generated link can be copied using the browser Clipboard API.

---

# 4️⃣ Visitor Opens the Link

When the tracking URL is visited, Flask receives:

```text
GET /click?url=...
```

The `/click` endpoint extracts:

* Target URL
* IP address
* User-agent
* Browser
* Platform
* IP-based geographic information

The server then renders the capture page with this information embedded into the page.

---

# 5️⃣ Browser Information Detection

The application analyzes the visitor's user-agent string.

Supported browser detection includes:

* Microsoft Edge
* Opera
* Chrome
* Firefox
* Safari

Supported platform detection includes:

* Windows
* Android
* iOS
* macOS
* Linux

This is handled by the `parse_ua()` helper function.

---

# 6️⃣ IP Geolocation

The server also performs IP-based geolocation.

The returned information includes:

```text
IP
City
Region
Country
ISP
Latitude
Longitude
```

If the IP-geolocation request fails, the application returns empty location values instead of stopping the application.

This location should be treated as **approximate**, not equivalent to GPS.

---

# 7️⃣ Browser GPS Location

The frontend uses:

```javascript
navigator.geolocation.watchPosition()
```

with:

```javascript
{
    enableHighAccuracy: true,
    timeout: Infinity,
    maximumAge: 0
}
```

The application attempts to obtain the most accurate browser-provided position available.

The project defines a precise-location threshold of:

```text
150 meters
```

Readings worse than this threshold are treated as approximate and are not immediately recorded as the preferred GPS result.

The application can continue collecting readings and select the reading with the best accuracy.

An excellent reading of `20m` accuracy or better can cause the process to finish early.

---

# 8️⃣ Reverse Geocoding

Once GPS coordinates are obtained, the application sends them to a reverse-geocoding service.

For example:

```text
Latitude: 26.xxxxxx
Longitude: 75.xxxxxx
```

can be converted into:

```text
City
Region
Country
```

This makes the dashboard easier to understand than displaying coordinates alone.

---

# 9️⃣ Sending Data to Flask

The browser sends the collected information to:

```text
POST /log_location
```

The payload contains fields such as:

```json
{
    "ip_address": "...",
    "latitude": 0,
    "longitude": 0,
    "accuracy": 0,
    "city": "...",
    "region": "...",
    "country": "...",
    "isp": "...",
    "source": "gps",
    "user_agent": "...",
    "browser": "...",
    "platform": "...",
    "redirect_url": "..."
}
```

The server validates that JSON data was received and inserts the record into SQLite.

---

# 🔟 Redirect

After the location data has been submitted, the frontend redirects the visitor to the destination URL.

The redirect logic is handled client-side:

```javascript
window.location.href = D.url || '/dashboard'
```

There is also a 60-second failsafe timer so that the visitor is not left indefinitely on the loading page.

---

# 📊 Dashboard

The `/dashboard` route provides the administration interface.

It calculates:

### Total Visits

```sql
SELECT COUNT(*) FROM visitors
```

### Unique IPs

```sql
SELECT COUNT(DISTINCT ip_address) FROM visitors
```

### GPS Locks

```sql
SELECT COUNT(*)
FROM visitors
WHERE location_source='gps'
```

The latest 100 visitor records are displayed.

---

# 🗺️ Interactive Map

The dashboard uses **Leaflet.js** to display visitor coordinates.

Each location becomes a map marker.

The map can automatically adjust its viewport to include the collected markers.

Coordinates can also be opened directly in Google Maps.

---

# 📋 Dashboard Table

The dashboard displays:

* Record ID
* IP address
* Coordinates
* GPS accuracy
* City/region
* Location source
* Browser
* Platform
* Redirect URL
* Timestamp
* Delete button

The interface distinguishes between:

```text
📡 GPS
```

and:

```text
🌐 IP
```

location sources.

---

# 🗑️ Delete Records

Individual visitor records can be deleted through:

```text
DELETE /delete/<visitor_id>
```

The server executes a parameterized SQL delete operation and returns JSON indicating success or failure.

The dashboard then removes the row without requiring a complete page reload.

---

# 🔌 API

The project also exposes:

```text
GET /api/visitors
```

This endpoint returns the latest 50 visitor records in JSON format.

Example response structure:

```json
{
    "status": "ok",
    "visitors": [
        {
            "id": 1,
            "ip_address": "...",
            "latitude": 0,
            "longitude": 0,
            "accuracy_meters": 20,
            "city": "...",
            "region": "...",
            "country": "...",
            "location_source": "gps"
        }
    ]
}
```

The API implementation reads the latest 50 database records and converts SQLite rows into dictionaries.

---

# 🔐 HTTPS Implementation

Browser geolocation generally requires a secure context.

The application therefore supports HTTPS using:

```text
cert.pem
key.pem
```

When both files exist, Python creates an SSL server context:

```python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(cert, key)
```

and starts Flask with that SSL context.

If the certificate files are missing, the application falls back to HTTP and prints a warning that GPS functionality may not work.

---

# 🚀 Installation

## 1. Install Python

Install Python 3.x on your system.

Verify:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## 2. Create a Project Directory

```bash
mkdir visitor-tracker
cd visitor-tracker
```

Place the project files inside the directory.

---

## 3. Create a Virtual Environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 4. Install Flask

```bash
pip install flask
```

The project primarily depends on Flask and Python's standard-library modules.

---

# 🔑 SSL Certificate Setup

For HTTPS testing, place your certificate and private key in the project directory:

```text
cert.pem
key.pem
```

The application expects these exact filenames.

### Important

Do **not** publish your private key.

Add this to `.gitignore`:

```gitignore
venv/
__pycache__/
*.pyc
visitor_data.db
key.pem
cert.pem
.env
```

If the private key has ever been accidentally uploaded to GitHub or another public location, revoke/replace the certificate/key pair.

---

# ▶️ Running the Application

Start the application with:

```bash
python dot.py
```

If HTTPS certificates are available, the application prints addresses similar to:

```text
HTTPS server ready — GPS will work!

Local:  https://127.0.0.1:5000
Phone:  https://YOUR-LAN-IP:5000
```

The Flask application listens on:

```text
0.0.0.0:5000
```

when HTTPS is enabled.

---

# 🌐 Available Routes

| Route           | Method | Purpose                 |
| --------------- | ------ | ----------------------- |
| `/`             | GET    | Home page               |
| `/generate`     | GET    | Tracking-link generator |
| `/click`        | GET    | Tracking/capture page   |
| `/log_location` | POST   | Save visitor location   |
| `/dashboard`    | GET    | Visitor dashboard       |
| `/api/visitors` | GET    | Visitor JSON API        |
| `/delete/<id>`  | DELETE | Delete visitor record   |

---

# 🧪 Local Testing

After starting the server:

```text
https://127.0.0.1:5000
```

Open the homepage.

Then test:

```text
/generate
```

Create a destination URL and use the generated link in an authorized test environment.

For mobile testing, connect the phone and computer to the same network and use the LAN address printed by the application.

Because browser geolocation is security-sensitive, HTTPS configuration and browser permissions are important.

---

# ☁️ Tunnel / Remote Testing

The source contains a note showing that the project can be exposed through a Cloudflare Tunnel using:

```bash
cloudflared tunnel --url https://localhost:5000 --no-tls-verify
```

This should only be used for authorized testing and demonstrations.

Do not expose a visitor-data dashboard publicly without authentication and proper access controls.

---

# 🧠 Key Concepts Demonstrated

This project is useful for learning several web-development concepts:

### Backend

* Flask routing
* HTTP GET/POST/DELETE
* JSON APIs
* SQLite CRUD operations
* Database initialization
* Error handling
* User-agent parsing
* HTTPS configuration

### Frontend

* HTML/CSS
* JavaScript
* Fetch API
* Browser Geolocation API
* Clipboard API
* Dynamic DOM manipulation
* Responsive design
* CSS animations

### Networking

* Client IP detection
* LAN IP detection
* HTTPS
* External HTTP APIs
* Reverse geocoding
* Web tunneling

### Data Visualization

* Leaflet.js
* Geographic coordinates
* Interactive markers
* Map viewport fitting
* Visitor statistics

---

# 🔒 Security Considerations

The current project is primarily a demonstration/prototype and should **not** be deployed directly as a production visitor analytics platform.

Recommended improvements include:

### Authentication

Protect:

```text
/dashboard
/api/visitors
/delete/<id>
```

with administrator authentication.

### Authorization

Do not allow arbitrary users to access or delete visitor information.

### Input Validation

The supplied redirect URL should be strictly validated before being used.

### HTTPS

Always use a trusted certificate in production.

### Database Security

Restrict access to:

```text
visitor_data.db
```

and never expose it directly through the web server.

### Privacy

Provide:

* Clear consent
* Privacy notice
* Data-retention policy
* Data deletion mechanism
* Appropriate legal basis for collecting location information

### Sensitive Data

IP addresses and precise coordinates can constitute sensitive personal information depending on jurisdiction and context. Minimize collection and retention to what is actually required.

---

# ⚠️ Current Implementation Limitations

The source reveals several areas that should be improved before production use:

1. The dashboard has no authentication.
2. The delete endpoint has no authentication or authorization.
3. The API endpoint exposes visitor information without authentication.
4. The redirect URL is accepted from the request.
5. The application uses Flask's development server with `debug=True`.
6. The IP geolocation request uses an external service.
7. Precise location can be stored when the browser provides it.
8. SSL certificates are loaded directly from local files.
9. There is no rate limiting.
10. There is no CSRF protection for state-changing operations.
11. There is no formal data-retention mechanism.
12. There is no consent-management system.
13. The current capture UI imitates a third-party game interface, which creates a significant transparency/privacy concern.

The Flask server is explicitly launched with `debug=True` in the current source, so that should be changed for production deployment.

---

# 🔮 Possible Future Improvements

## Security

* Add Flask-Login authentication
* Add admin sessions
* Add CSRF protection
* Add rate limiting
* Add URL allowlists
* Add secure headers
* Disable debug mode
* Add access logs
* Encrypt sensitive stored information where appropriate

## Database

Move from SQLite to:

```text
PostgreSQL
```

for larger deployments.

Add:

* Indexes
* Data retention
* Pagination
* Automatic cleanup
* Export functionality

## Dashboard

Add:

* Search
* Filtering
* Date ranges
* Visitor charts
* Country statistics
* Browser statistics
* Platform statistics
* CSV export
* Real-time updates

## Privacy

Add a transparent consent page explaining:

```text
What data is collected
Why it is collected
How long it is stored
Who can access it
How the visitor can request deletion
```

---

# 📚 Learning Outcomes

After building this project, you can understand how to:

* Build a Flask web application
* Create REST-style endpoints
* Work with SQLite
* Process JSON requests
* Use browser APIs
* Request geographic coordinates
* Perform reverse geocoding
* Integrate external APIs
* Parse user-agent information
* Build an interactive map
* Serve a Flask application over HTTPS
* Build a complete frontend without React/Vue
* Connect browser JavaScript with a Python backend
* Design a basic analytics dashboard

---

# 🏁 Project Flow Summary

```text
Start Flask
     │
     ▼
Initialize SQLite
     │
     ▼
Open Home Page
     │
     ▼
Generate Destination Link
     │
     ▼
Authorized Visitor Opens Link
     │
     ▼
Collect Browser Metadata
     │
     ├───────────────┐
     ▼               ▼
IP Geolocation    Browser GPS
     │               │
     └───────┬───────┘
             ▼
       Reverse Geocode
             │
             ▼
       POST /log_location
             │
             ▼
        SQLite Storage
             │
             ▼
         Dashboard
             │
       ┌─────┴─────┐
       ▼           ▼
     Table        Map
       │
       ▼
 Delete Records
```

---

# 📄 License

If this project is published publicly, add a license appropriate to your intended use, such as the MIT License.

Before publishing, remove:

```text
cert.pem
key.pem
visitor_data.db
```

and any other files containing private credentials or real visitor information.

---

# 👨‍💻 Author

**Geetansh Singh**

Built as a Python/Flask web-development and location-technology project.

---

## ⚠️ Responsible Use

This project should be used for:

* Your own devices
* Authorized demonstrations
* Development/testing environments
* Security research with permission
* Consent-based analytics

It should **not** be used to secretly obtain another person's precise location, impersonate a service to trick someone into providing location access, or collect personal information without appropriate authorization and consent.

