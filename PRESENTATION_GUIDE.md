# Nyayamrit Deployment Presentation Guide

## 🎯 Quick Start for Presentations

### Option 1: One-Click Launch (Windows)
```bash
# Double-click or run from command prompt
start_demo.bat
```

### Option 2: One-Click Launch (Linux/Mac)
```bash
# Make executable and run
chmod +x start_demo.sh
./start_demo.sh
```

### Option 3: Manual Launch
```bash
# Start the presentation servers
cd web_interface
python start_presentation.py
```

## 📊 Presentation URLs

Once started, you'll have access to:

### 🖥️ Main Demo Dashboard
**URL:** http://127.0.0.1:8080

**Features:**
- System overview and real-time statistics
- Knowledge graph metrics (107 sections, 47 definitions, 35 rights)
- Performance monitoring and uptime tracking
- Recent query activity feed
- Quick access to all demo features

### 🚀 Interactive Live Demo
**URL:** http://127.0.0.1:8080/demo/live

**Features:**
- Role-based query interface (Citizen, Lawyer, Judge)
- Pre-loaded example questions for each audience
- Real-time query processing with GraphRAG pipeline
- Citation display with confidence scoring
- Response validation and human review flagging

### 📚 API Documentation
**URL:** http://127.0.0.1:8000/docs

**Features:**
- Interactive Swagger UI documentation
- All REST API endpoints with examples
- Authentication testing interface
- Real-time API testing capabilities

### 🔍 System Health Monitor
**URL:** http://127.0.0.1:8080/demo/health

**Features:**
- Comprehensive system health checks
- Component status monitoring
- Knowledge graph validation results
- Performance metrics and statistics

## 🎪 Demo Scenarios

### Scenario 1: Citizen Query Demo
1. Go to http://127.0.0.1:8080/demo/live
2. Select "Citizen" role
3. Try example: "What is a consumer according to CPA 2019?"
4. Show simple, accessible explanation with legal citations
5. Highlight confidence scoring and validation

### Scenario 2: Lawyer Research Demo
1. Switch to "Lawyer" role
2. Try example: "Show me Section 2 of Consumer Protection Act 2019"
3. Demonstrate detailed legal analysis with cross-references
4. Show citation validation and export capabilities
5. Access API documentation for integration

### Scenario 3: System Architecture Demo
1. Visit main dashboard at http://127.0.0.1:8080
2. Show real-time statistics and knowledge graph metrics
3. Demonstrate system health monitoring
4. Explain GraphRAG architecture and validation layer
5. Show performance metrics and scalability features

### Scenario 4: API Integration Demo
1. Go to http://127.0.0.1:8000/docs
2. Demonstrate REST API endpoints
3. Show authentication and role-based access
4. Test query processing with different audiences
5. Explain integration possibilities for legal tech

## 🔧 Technical Highlights to Showcase

### GraphRAG Architecture
- **Knowledge Graph**: 107 sections, 127 clauses, 47 definitions, 35 rights from CPA 2019
- **Graph Traversal**: Multi-hop reasoning with citation preservation
- **Validation Layer**: Hallucination detection and confidence scoring
- **Response Grounding**: All outputs verified against knowledge graph

### Multi-Audience Support
- **Citizens**: Simple explanations with legal disclaimers
- **Lawyers**: Detailed analysis with citation validation
- **Judges**: Comprehensive reasoning with audit trails

### Security & Compliance
- **JWT Authentication**: Role-based access control
- **Anonymous Access**: Public queries for citizens
- **Audit Logging**: Comprehensive interaction tracking
- **Data Protection**: Privacy-compliant design

### Performance & Scalability
- **Fast Responses**: <3s for simple queries, <10s for complex
- **Concurrent Users**: Supports 1000+ simultaneous users
- **Caching**: Optimized knowledge graph access
- **Monitoring**: Real-time performance metrics

## 📋 Presentation Checklist

### Before Starting
- [ ] Ensure Python 3.9+ is installed
- [ ] All dependencies are installed (`pip install -r web_interface/requirements.txt`)
- [ ] Knowledge graph data is present in `knowledge_graph/` directory
- [ ] Port 8000 and 8080 are available

### During Presentation
- [ ] Start with main dashboard overview
- [ ] Demonstrate different user roles (citizen → lawyer → judge)
- [ ] Show real-time statistics and monitoring
- [ ] Highlight GraphRAG architecture benefits
- [ ] Demonstrate API documentation and integration
- [ ] Show system health and validation features

### Key Talking Points
1. **Problem**: Legal complexity and accessibility barriers in India
2. **Solution**: GraphRAG-based AI assistant with knowledge graph grounding
3. **Innovation**: Hallucination mitigation through graph validation
4. **Impact**: Democratizing legal access across language barriers
5. **Scalability**: Ready for expansion to full Indian legal corpus

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the ports
netstat -ano | findstr :8000
netstat -ano | findstr :8080

# Kill processes if needed (Windows)
taskkill /PID <process_id> /F
```

**Import Errors:**
```bash
# Install missing dependencies
pip install -r web_interface/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**Knowledge Graph Not Loading:**
- Ensure `knowledge_graph/` directory exists
- Check that JSON files are present and valid
- Look for error messages in server logs

**API Not Responding:**
- Wait 30 seconds for full startup
- Check server logs for errors
- Verify all dependencies are installed

### Performance Optimization

**For Large Audiences:**
- Use production WSGI server (gunicorn/uvicorn)
- Enable caching and load balancing
- Monitor memory usage and optimize queries

**For Slow Responses:**
- Check knowledge graph size and indexing
- Monitor LLM API latency (if configured)
- Optimize graph traversal algorithms

## 📞 Support

For technical issues during presentation:
1. Check server logs in terminal
2. Verify all services are running
3. Test with simple queries first
4. Use health check endpoint for diagnostics

## 🎉 Success Metrics

A successful presentation should demonstrate:
- ✅ Fast, accurate responses to legal queries
- ✅ Proper citation and validation of all claims
- ✅ Multi-audience support with appropriate language
- ✅ Real-time system monitoring and health checks
- ✅ Scalable architecture ready for production deployment

---

**Ready to showcase the future of legal AI assistance in India! 🇮🇳⚖️🤖**