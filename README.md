# VisionExtract - AI-Powered Document Processing RESTful API

A robust RESTful API that uses AI to extract text and structured data from handwritten or typed images, convert tables into clean CSV or JSON format, and intelligently upscale image quality for enhanced clarity and professional-grade results.

## 🌟 Features

### Core Functionality
- **Text Extraction**: Extract text from images (handwritten or printed) using AWS Textract
- **Table Data Extraction**: Convert table images into structured CSV/JSON data with automatic cleaning
- **Image Upscaling**: Enhance image quality using Real-ESRGAN AI models (4x upscaling)
- **Multi-format Support**: Handle various image formats including PNG, JPG, JPEG
- **Batch Processing**: Process multiple images simultaneously
- **Database Storage**: Track all processing history with metadata

### Technical Features
- **RESTful API**: Clean, documented endpoints with authentication
- **Dual Authentication**: Bearer token and Basic authentication support
- **SQLite Database**: Persistent storage of processing history
- **File Management**: Organized input/output directory structure
- **Error Handling**: Comprehensive error handling and validation
- **Bootstrap UI**: Modern, responsive web interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- AWS Account with Textract access
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/visionextract-api.git
   cd visionextract-api
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   FLASK_KEY=your_flask_secret_key
   FLASK_KEY_V1=your_api_v1_secret_key
   API_KEY=your_api_bearer_token
   BASIC_KEY=your_basic_auth_token
   BASIC_AUTH_USERNAME=your_username
   BASIC_AUTH_PASSWORD=your_password
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=your_aws_region
   ```

5. **Run the application**
   ```bash
   # Web interface
   python main.py
   
   # RESTful API only
   python api.py
   ```

## 📖 API Documentation

### Authentication
The API supports two authentication methods:
- **Bearer Token**: Include `Authorization: Bearer <your_token>` in headers
- **Basic Auth**: Include `Authorization: Basic <your_basic_key>` in headers

### Endpoints

#### Web Interface
- `GET /` - Main application interface
- `GET /functions` - Function selection menu
- `GET /documentation` - API documentation
- `GET /history_images` - View processed image history
- `GET /history_tables` - View processed table history
- `GET /history_text` - View processed text history

#### RESTful API (v1)
- `GET /v1/` - API home page
- `GET /v1/history_images` - Get all processed image files
- `GET /v1/history_text` - Get all processed text files
- `GET /v1/history_tables` - Get all processed table files
- `POST /v1/upscale` - Upscale images (requires file upload)
- `POST /v1/extract_text` - Extract text from images (requires file upload)
- `POST /v1/extract_table` - Extract table data from images (requires file upload)

### Usage Examples

#### Extract Text from Image
```bash
curl -X POST "http://localhost:5000/v1/extract_text" \
  -H "Authorization: Bearer your_token" \
  -F "file=@image.jpg"
```

#### Upscale Image
```bash
curl -X POST "http://localhost:5000/v1/upscale" \
  -H "Authorization: Bearer your_token" \
  -F "file=@image.jpg"
```

#### Extract Table Data
```bash
curl -X POST "http://localhost:5000/v1/extract_table" \
  -H "Authorization: Bearer your_token" \
  -F "file=@table_image.jpg"
```

## 🏗️ Project Structure

```
visionextract-api/
├── main.py                 # Main Flask application (web interface)
├── api.py                  # RESTful API endpoints
├── methods.py              # Core processing functions
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── input/                  # Input image directory
├── output/                 # Processed output directory
├── static/                 # Static assets (images, videos)
├── templates/              # HTML templates
├── instance/               # Database files
└── Image Upscaler/        # Real-ESRGAN integration
    ├── main.py
    └── Real-ESRGAN/       # AI upscaling models
```

## 🔧 Configuration

### Database
The application uses SQLite with the following schema:
- **Extract Table**: Stores processing history with metadata
- Fields: id, name, filetype, date, file_location, output_location, input_size, output_size, text_output, data_output, edit_date

### File Limits
- **Image Upload**: Maximum 10 images per batch
- **File Size**: Maximum 100KB per image
- **Supported Formats**: PNG, JPG, JPEG

## 🛠️ Dependencies

### Core Dependencies
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Bootstrap5**: UI framework
- **Boto3**: AWS SDK for Textract
- **Pandas**: Data manipulation
- **Pillow**: Image processing
- **Python-dotenv**: Environment variable management

### AI Models
- **Real-ESRGAN**: Image upscaling models
- **AWS Textract**: OCR and table extraction

## 🚀 Deployment

### Local Development
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python main.py
```

### Production
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation at `/documentation` endpoint
- Review the API examples in the templates

## 🔮 Roadmap

- [ ] Add support for PDF documents
- [ ] Implement real-time processing status
- [ ] Add more AI models for specialized tasks
- [ ] Create mobile-responsive web app
- [ ] Add batch processing queue system
- [ ] Implement user management and quotas

---

**Built with ❤️ using Flask, AWS Textract, and Real-ESRGAN**
