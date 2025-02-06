# Flask File Sharing Webapp

This project is a file-sharing application developed using Flask. Users can upload files and share them via a unique download link. The files are available for download for 24 hours, after which they are automatically deleted.

## Features

- **Dynamic Chunk Uploads:** Files are uploaded in dynamically sized chunks, optimizing the upload process for different file sizes.
- **Timeout:** Uploaded files are automatically deleted after 24 hours.
- **Parallel Download:** Users can download files in parallel chunks for faster download speeds.
- **Security:** The application enforces HTTPS and includes security headers to protect against common web vulnerabilities.
- **Cloudflare Tunnel Integration:** The application can be exposed to the internet securely using Cloudflare Tunnel, ensuring secure and reliable access.

## Images
![File Upload Page](https://github.com/user-attachments/assets/b5134b1f-02dc-4e27-bfaa-d1d896f2bcca)
![Upload Successfull Page](https://github.com/user-attachments/assets/69eba7b0-4700-42b0-ad95-9ce162629c68)
![Download Page](https://github.com/user-attachments/assets/733b3d61-e9c9-46bd-9310-7c4b34e8fd1c)

## How It Works

The application allows users to upload files, which are split into chunks for efficient handling. Once uploaded, a unique download link is generated. The link is valid for 24 hours, after which the file is automatically deleted. The application also supports parallel downloads, allowing users to download files faster by splitting them into chunks.

### Dynamic Chunk Uploads

Files are uploaded in dynamically sized chunks based on the file size:

- For files larger than **1GB**, chunks are **25MB**.
- For files between **512MB and 1GB**, chunks are **20MB**.
- For smaller files, chunks are **15MB**.

This dynamic approach ensures efficient uploads regardless of the file size.

### Cloudflare Tunnel Integration

To securely expose the application to the internet, you can use Cloudflare Tunnel. Cloudflare Tunnel creates a secure connection between your application and the Cloudflare network, allowing users to access your application without exposing your server's IP address.

#### Steps to Set Up Cloudflare Tunnel:

1. **Install Cloudflare Tunnel:** Follow the official guide to install the Cloudflare Tunnel client on your server.
2. **Create a Tunnel:** Use the Cloudflare dashboard to create a new tunnel and configure it to point to your Flask application (e.g., `localhost:5000`).
3. **Secure Your Application:** Cloudflare Tunnel automatically provides HTTPS and DDoS protection, ensuring your application is secure and accessible.

## Installation

### Prerequisites

- Python 3.7 or higher
- Flask
- Cloudflare Tunnel (optional, for secure internet access)

### Steps

#### Clone the Repository:

```bash
git clone https://github.com/mre31/FlaskFileShare.git
cd flask-file-sharing-app
```

#### Set Up a Virtual Environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

#### Install Dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

You can start the application in multiple ways:

### Option 1: Running `app.py` Directly

You can start the application by directly running the `app.py` file using Python:

```bash
python app.py
```

This will start the Flask development server, and the application will be accessible at `http://localhost:5000`.

### Option 2: Using a `run.bat` File (Windows)

For convenience, you can create a `run.bat` file to start the application. This is especially useful on Windows systems.

. Double-click the `run.bat` file to start the application. It will activate the virtual environment and run `app.py`.

## Usage

### Upload a File:

1. Go to the homepage and select a file to upload.
2. Once uploaded, a unique download link will be generated.

### Share the Link:

- Share the generated link with others. The link will be valid for 24 hours.

### Download a File:

- Use the provided link to download the file. The application supports parallel downloads for faster speeds.

## Configuration

### Environment Variables

- `PREFERRED_URL_SCHEME`: Set to `https` to enforce HTTPS (default: `https`).
- `UPLOAD_FOLDER`: The directory where uploaded files are stored (default: `uploads`).
- `TEMP_FOLDER`: The directory for temporary chunk storage (default: `temp_chunks`).

### Security Headers

The application includes the following security headers:

- `Strict-Transport-Security`: Enforces HTTPS.
- `X-Content-Type-Options`: Prevents MIME type sniffing.
- `X-Frame-Options`: Protects against clickjacking.
- `Referrer-Policy`: Controls referrer information.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the **BSD-3-Clause License**. See the [LICENSE](https://github.com/mre31/FlaskFileShare?tab=BSD-3-Clause-1-ov-file) file for details.
