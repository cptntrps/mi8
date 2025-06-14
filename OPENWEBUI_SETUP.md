# 🔗 Open WebUI + AgenticSeek Integration - SETUP GUIDE

## ✅ **SERVICES RUNNING**
- 🔧 **AgenticSeek API**: http://localhost:8000 ✅ READY
- 💬 **Open WebUI**: http://localhost:8080 ✅ READY
- 🎨 **Dashboard**: http://localhost:9000 ✅ READY

## 📋 **Step-by-Step Open WebUI Setup**

### **Step 1: Access Open WebUI**
1. Open your browser
2. Go to: **http://localhost:8080**
3. Create an account or sign in if you already have one

### **Step 2: Configure AgenticSeek API Connection**
1. Click the **Settings gear icon** (⚙️) in the top right
2. Go to **Settings** → **Connections**
3. Find the **"OpenAI API"** section
4. Configure:
   ```
   API Base URL: http://localhost:8000
   API Key: agenticsseek-demo-key
   ```
5. Click **"Verify Connection"** - you should see ✅ success

### **Step 3: Select AgenticSeek Models**
1. Go to **Settings** → **Models**
2. You should now see AgenticSeek models:
   - **agenticsseek-enhanced** (General purpose)
   - **agenticsseek-database** (Database specialist)
3. Select a model from the dropdown

### **Step 4: Start Chatting!**
1. Go back to the main chat interface
2. Make sure your selected model shows in the top bar
3. Try these example prompts:

## 🧪 **Test Prompts for Open WebUI**

### **General Capabilities**
```
Hello! What can you help me with?
```

### **Database Operations**
```
I need help with database operations. Can you connect to a database and show me what you can do?
```

### **File Management**
```
Show me your file management capabilities. How can you help with Cursor IDE integration?
```

### **Voice Features**
```
Tell me about your voice command capabilities. What voice commands do you support?
```

## 🔧 **Troubleshooting**

### **"No models available" or "Connection failed"**
1. Verify AgenticSeek API is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check the API base URL is exactly: `http://localhost:8000`
3. Use API key: `agenticsseek-demo-key`

### **"Model not responding"**
1. Check API logs for errors
2. Try the test command:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer agenticsseek-demo-key" \
     -d '{
       "model": "agenticsseek-enhanced",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
   ```

### **Connection Issues**
1. Ensure both services are running:
   ```bash
   # Check AgenticSeek API
   curl http://localhost:8000/health
   
   # Check Open WebUI
   curl http://localhost:8080/health
   ```

## 🎯 **Expected Results**

Once configured correctly, you should see:

1. **✅ Model Selection**: AgenticSeek models in the dropdown
2. **✅ Chat Responses**: Intelligent responses from selected agent
3. **✅ Capabilities**: Agent explains its database, file, and voice features
4. **✅ OpenAI Format**: Responses formatted properly in chat interface

## 🚀 **Advanced Features Available**

### **Database Agent** (`agenticsseek-database`)
```
Connect to my SQLite database and show me the table structure
```

### **Enhanced MCP Agent** (`agenticsseek-enhanced`)
```
Help me open a file in Cursor and remember what I'm working on
```

### **Voice Integration**
```
What voice commands can I use to control the system?
```

## 🎉 **Success Confirmation**

You'll know the integration is working when:

1. ✅ AgenticSeek models appear in Open WebUI model dropdown
2. ✅ Chat responses mention specific AgenticSeek capabilities
3. ✅ Agent explains database, file, and voice features
4. ✅ Responses are contextual and agent-specific

## 📞 **Quick Test**

Try this conversation in Open WebUI:

**You**: "Hello! Tell me about your capabilities."

**Expected Response**: The agent should introduce itself and list its specific capabilities like database operations, file management, voice commands, etc.

---

## 🎊 **Integration Complete!**

**AgenticSeek is now fully integrated with Open WebUI!**

You now have:
- 💬 **Professional chat interface** via Open WebUI
- 🤖 **Advanced AI agents** via AgenticSeek
- 🎤 **Voice capabilities** ready to use
- 🗄️ **Database operations** available
- 📁 **File management** integrated

**Start chatting and explore the full power of AgenticSeek through Open WebUI!**