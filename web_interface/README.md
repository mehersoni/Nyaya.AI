# Nyayamrit Web Interface

This directory contains the FastAPI backend and React frontend for the Nyayamrit GraphRAG-based judicial assistant system.

## Backend (FastAPI)

The FastAPI backend provides REST API endpoints for:
- Natural language query processing
- Section and definition retrieval
- Citation validation
- User authentication and authorization
- Health monitoring

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the server:**
   ```bash
   python run_server.py
   ```

4. **Test the API:**
   ```bash
   python test_api.py
   ```

5. **View API documentation:**
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info

#### Core Functionality
- `POST /api/v1/query` - Process natural language queries
- `GET /api/v1/section/{section_id}` - Retrieve specific section
- `GET /api/v1/definition/{term}` - Look up legal definitions
- `POST /api/v1/validate-citations` - Validate legal citations (lawyers only)

#### System
- `GET /health` - Health check
- `GET /` - API information

### Authentication & Authorization

The system implements role-based access control (RBAC) with three user roles:

1. **Citizen** (anonymous allowed)
   - Basic query access
   - No registration required for basic features

2. **Lawyer** (registration required)
   - All citizen features
   - Advanced search capabilities
   - Citation validation
   - API access for integrations

3. **Judge** (registration required)
   - All lawyer features
   - Secure case analysis (Phase 4)
   - Precedent search (Phase 4)
   - Audit log access

### Default Test Accounts

For development and testing:

- **Citizen**: `citizen@example.com` / `citizen123`
- **Lawyer**: `lawyer@example.com` / `lawyer123`
- **Judge**: `judge@example.com` / `judge123`

### Configuration

Key environment variables:

- `OPENAI_API_KEY` - Required for LLM functionality
- `JWT_SECRET_KEY` - Required for authentication security
- `BHASHINI_API_KEY` - Optional for multilingual support
- `KNOWLEDGE_GRAPH_PATH` - Path to knowledge graph data

## Frontend (React)

A React-based citizen-focused chat interface for the Nyayamrit GraphRAG-based judicial assistant system.

## Features

- **Conversational Chat Interface**: Natural language queries with conversational flow
- **Multilingual Support**: 10+ Indian languages via language selector
- **Clickable Citations**: Interactive legal citations with visual distinction
- **Example Questions**: Contextual example questions for common citizen queries
- **Disclaimer System**: Prominent legal disclaimers and user acceptance flow
- **Feedback System**: User feedback collection with thumbs up/down and detailed feedback
- **Report Issue**: Issue reporting system for inaccurate information or technical problems
- **Accessibility**: WCAG 2.1 Level AA compliance with keyboard navigation and screen reader support
- **Responsive Design**: Mobile-friendly interface that works on all devices

## Technology Stack

- **React 18** with TypeScript
- **Chakra UI** for component library and accessibility
- **Redux Toolkit** for state management
- **React Markdown** for response formatting
- **Axios** for API communication
- **React Icons** for iconography

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will open at `http://localhost:3000`.

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

## Architecture

### State Management

The application uses Redux Toolkit with two main slices:

- **chatSlice**: Manages chat messages, queries, and conversation state
- **uiSlice**: Manages UI state like modals, disclaimers, and sidebar

### Component Structure

```
src/
├── components/
│   ├── Chat/
│   │   ├── ChatInterface.tsx      # Main chat container
│   │   ├── ChatWindow.tsx         # Message display area
│   │   ├── MessageBubble.tsx      # Individual message component
│   │   ├── QueryInput.tsx         # User input component
│   │   ├── ExampleQuestions.tsx   # Suggested questions
│   │   ├── ResponseDisplay.tsx    # Formatted response display
│   │   └── CitationLink.tsx       # Clickable citation component
│   ├── Disclaimer/
│   │   ├── DisclaimerBanner.tsx   # Persistent disclaimer banner
│   │   └── DisclaimerModal.tsx    # Initial disclaimer modal
│   ├── Feedback/
│   │   └── FeedbackModal.tsx      # User feedback collection
│   ├── Header/
│   │   └── Header.tsx             # Application header
│   ├── Language/
│   │   └── LanguageSelector.tsx   # Language selection dropdown
│   └── ReportIssue/
│       └── ReportIssueModal.tsx   # Issue reporting modal
├── store/
│   ├── store.ts                   # Redux store configuration
│   └── slices/
│       ├── chatSlice.ts           # Chat state management
│       └── uiSlice.ts             # UI state management
├── theme/
│   └── theme.ts                   # Chakra UI theme customization
└── App.tsx                        # Main application component
```

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **High Contrast Mode**: Support for high contrast display preferences
- **Reduced Motion**: Respects user's reduced motion preferences
- **Focus Management**: Clear focus indicators and logical tab order
- **Alternative Text**: Descriptive labels for all icons and images

## Multilingual Support

The interface supports 12 languages:

- English (en)
- Hindi (hi) - हिन्दी
- Tamil (ta) - தமிழ்
- Telugu (te) - తెలుగు
- Bengali (bn) - বাংলা
- Marathi (mr) - मराठी
- Gujarati (gu) - ગુજરાતી
- Kannada (kn) - ಕನ್ನಡ
- Malayalam (ml) - മലയാളം
- Punjabi (pa) - ਪੰਜਾਬੀ
- Odia (or) - ଓଡ଼ିଆ
- Assamese (as) - অসমীয়া

## Integration with Backend

The frontend is designed to integrate with the FastAPI backend through:

- **Query Processing**: Sends user queries to `/api/v1/query` endpoint
- **Citation Retrieval**: Fetches legal provisions via citation endpoints
- **Feedback Collection**: Submits user feedback for quality assurance
- **Issue Reporting**: Reports technical and content issues

## Development Guidelines

### Code Style

- Use TypeScript for type safety
- Follow React functional component patterns with hooks
- Use Chakra UI components for consistency
- Implement proper error boundaries and loading states

### Testing

- Unit tests for individual components
- Integration tests for user workflows
- Accessibility testing with automated tools
- Cross-browser compatibility testing

### Performance

- Lazy loading for non-critical components
- Memoization for expensive computations
- Optimized bundle size with code splitting
- Efficient state updates with Redux Toolkit

## Deployment

The application can be deployed to any static hosting service:

```bash
# Build for production
npm run build

# Deploy the build/ directory to your hosting service
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Ensure accessibility compliance
4. Test multilingual functionality
5. Update documentation as needed

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ GraphRAG Engine │
│                 │    │                 │    │                 │
│ • Chat UI       │◄──►│ • REST API      │◄──►│ • Query Parser  │
│ • Auth Forms    │    │ • Authentication│    │ • Graph Traversal│
│ • Citation View │    │ • Authorization │    │ • Context Builder│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Knowledge Graph │
                       │                 │
                       │ • Sections      │
                       │ • Definitions   │
                       │ • Rights        │
                       │ • References    │
                       └─────────────────┘
```

## Development

### Running in Development Mode

1. **Start the backend:**
   ```bash
   cd web_interface
   python run_server.py
   ```

2. **Start the frontend (in another terminal):**
   ```bash
   cd web_interface
   npm start
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/docs

### Testing

- **Backend tests:** `python test_api.py`
- **Frontend tests:** `npm test`
- **Integration tests:** Run both servers and test through UI

### Deployment

See deployment documentation for production setup with:
- Docker containers
- Kubernetes orchestration
- Load balancing
- SSL/TLS termination
- Database persistence

## Requirements Implementation

This implementation addresses the following requirements:

- **Requirement 5.1**: Web-based interface for citizens
- **Requirement 6.1**: Advanced tools for lawyers
- **Requirement 10.4**: Authentication and authorization
- **Requirement 2.1**: GraphRAG integration
- **Requirement 11.1**: Response validation

## Next Steps

1. **Phase 2**: Multilingual support via Bhashini API
2. **Phase 3**: Advanced lawyer tools and API integrations
3. **Phase 4**: Judge-focused features with case law analysis
4. **Production**: Deployment and monitoring setup