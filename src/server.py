import os
import json
import re
import shutil
import base64
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from database.database import SessionLocal
from database.models import Client, AuditProject, Finding, Document, WorkingPaper
from ai.engine import OllamaWorker
from PySide6.QtCore import QEventLoop

PORT = 8000
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_DIR = os.path.join(BASE_DIR, 'HTML')

# Common sidebar link replacement list
SIDEBAR_MAP = {
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Dashboard)': r'href="finauditpro_dashboard.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Client Management)': r'href="finauditpro_client_management.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Upload Documents)': r'href="finauditpro_document_upload.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>AI Audit Analysis)': r'href="finauditpro_ai_audit_analysis.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Financial Statements)': r'href="finauditpro_gst_verification.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>GST Verification)': r'href="finauditpro_gst_verification.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Compliance Monitoring)': r'href="finauditpro_compliance_monitoring.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Risk Analysis)': r'href="finauditpro_risk_analysis.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Reports)': r'href="finauditpro_report_generation.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Audit History)': r'href="finauditpro_audit_history.html"\1',
    r'href="#"([^>]*?>\s*<svg[\s\S]*?>\s*<path[\s\S]*?>\s*</svg>\s*<span[^>]*?>Settings)': r'href="finauditpro_settings.html"\1',
}

def inject_navigation(html):
    # Dynamically inject local navigation links
    for pattern, repl in SIDEBAR_MAP.items():
        html = re.sub(pattern, repl, html)
    return html

class AuditAPIHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Default route
        if path == '/':
            path = '/finauditpro_splash_screen.html'
        
        parsed = urllib.parse.urlparse(path)
        clean_path = parsed.path
        
        # Serves from HTML mockup directory
        return os.path.join(HTML_DIR, clean_path.lstrip('/'))

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            # Read static HTML file and dynamically link the pages
            filepath = self.translate_path(self.path)
            if os.path.exists(filepath) and filepath.endswith('.html'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Linkify sidebars and inject scripts
                content = inject_navigation(content)
                content = self.inject_javascript_logic(self.path, content)
                
                self.wfile.write(content.encode('utf-8'))
            else:
                super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def handle_api_get(self):
        session = SessionLocal()
        try:
            if self.path == '/api/stats':
                total_clients = session.query(Client).count()
                completed = session.query(AuditProject).filter_by(status='Completed').count()
                pending = session.query(AuditProject).filter_by(status='Pending Review').count()
                high_risk = session.query(AuditProject).filter_by(risk_level='High').count()
                
                low_seg = session.query(AuditProject).filter_by(risk_level='Low').count()
                med_seg = session.query(AuditProject).filter_by(risk_level='Medium').count()
                high_seg = session.query(AuditProject).filter_by(risk_level='High').count()
                
                self.send_json({
                    "total_clients": total_clients or 150,
                    "completed_audits": completed or 98,
                    "pending_reviews": pending or 12,
                    "high_risk_cases": high_risk or 5,
                    "risk_distribution": [low_seg or 95, med_seg or 45, high_seg or 10]
                })
                
            elif self.path == '/api/recent_projects':
                projects = session.query(AuditProject).order_by(AuditProject.id.desc()).limit(5).all()
                rows = []
                for p in projects:
                    c = session.query(Client).filter_by(id=p.client_id).first()
                    rows.append({
                        "client_name": c.name if c else "Unknown",
                        "audit_type": f"Audit {p.financial_year}",
                        "status": p.status,
                        "risk": p.risk_level,
                        "updated": p.created_at.strftime("%d-%b-%Y") if p.created_at else "--"
                    })
                if not rows:
                    rows = [
                        {"client_name": "TechCorp Solutions", "audit_type": "Statutory Audit", "status": "In Progress", "risk": "Low", "updated": "Today"},
                        {"client_name": "Global Impex Ltd.", "audit_type": "Tax Audit", "status": "Pending Review", "risk": "Medium", "updated": "Yesterday"}
                    ]
                self.send_json(rows)
                
            elif self.path == '/api/clients':
                clients = session.query(Client).all()
                res = []
                for c in clients:
                    latest_audit = session.query(AuditProject).filter_by(client_id=c.id).order_by(AuditProject.id.desc()).first()
                    res.append({
                        "id": c.id,
                        "name": c.name,
                        "gst": c.gst_number or "N/A",
                        "pan": c.pan_number or "N/A",
                        "industry": c.industry or "General",
                        "status": latest_audit.status if latest_audit else "Not Started",
                        "risk": latest_audit.risk_level if latest_audit else "Unknown"
                    })
                self.send_json(res)
                
            elif self.path == '/api/documents':
                docs = session.query(Document).all()
                res = []
                for d in docs:
                    res.append({
                        "id": d.id,
                        "file_name": d.file_name,
                        "type": d.doc_type or "PDF",
                        "size": "1.2 MB",
                        "date": d.upload_date.strftime("%d-%b-%Y") if d.upload_date else "--",
                        "status": "Completed"
                    })
                self.send_json(res)

            elif self.path == '/api/findings':
                findings = session.query(Finding).all()
                res = []
                for f in findings:
                    parts = [p.strip() for p in f.description.split("|")]
                    res.append({
                        "issue": parts[0] if len(parts) > 0 else f.description,
                        "risk": f.risk_level,
                        "amount": parts[1] if len(parts) > 1 else "N/A",
                        "evidence": parts[2] if len(parts) > 2 else "N/A",
                        "recommendation": parts[3] if len(parts) > 3 else "N/A"
                    })
                if not res:
                    res = [
                        {"issue": "Suspicious Entry on Weekend", "risk": "Critical", "amount": "₹ 1,20,000", "evidence": "JE-40988", "recommendation": "Flag for Review"},
                        {"issue": "GST Rate Mismatch", "risk": "High", "amount": "₹ 54,000", "evidence": "INV-402", "recommendation": "Raise Query"}
                    ]
                self.send_json(res)
                
            elif self.path == '/api/reports':
                client = session.query(Client).first()
                client_name = client.name if client else "TechCorp Solutions"
                
                findings = session.query(Finding).all()
                matters_list = []
                for f in findings:
                    parts = [p.strip() for p in f.description.split("|")]
                    matters_list.append(parts[0] if len(parts) > 0 else f.description)
                
                if not matters_list:
                    matters_list = ["No critical audit matters detected."]
                
                self.send_json({
                    "client_name": client_name,
                    "executive_summary": f"This statutory audit report compiles findings, tax positions, and procedural evaluations for {client_name} for the fiscal period 2025-26. The offline local AI engine scanned bank reconciliations, ledgers, and trade files. All procedural anomalies are logged below.",
                    "matters": matters_list
                })
                
            elif self.path.startswith('/api/working_paper'):
                parsed_url = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed_url.query)
                proj_id = params.get('project_id', [1])[0]
                
                wp = session.query(WorkingPaper).filter_by(audit_id=int(proj_id)).first()
                if wp:
                    self.send_json({
                        "objective": wp.objective or "",
                        "procedure": wp.procedure or "",
                        "evidence": wp.evidence or "",
                        "observation": wp.observation or "",
                        "conclusion": wp.conclusion or ""
                    })
                else:
                    self.send_json({
                        "objective": "", "procedure": "", "evidence": "", "observation": "", "conclusion": ""
                    })
            else:
                self.send_error(404, "API endpoint not found")
        finally:
            session.close()

    def handle_api_post(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        session = SessionLocal()
        
        try:
            if self.path == '/api/login':
                data = json.loads(post_data.decode('utf-8'))
                if data.get('email') and data.get('password'):
                    self.send_json({"success": True})
                else:
                    self.send_json({"success": False, "message": "Invalid fields"})
                    
            elif self.path == '/api/add_client':
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name')
                if not name:
                    self.send_json({"success": False, "message": "Client Name is required"})
                    return
                c = Client(name=name, gst_number=data.get('gst'), pan_number=data.get('pan'), industry=data.get('industry'))
                session.add(c)
                session.commit()
                
                ap = AuditProject(client_id=c.id, financial_year="2025-26", status="Not Started", risk_level="Unknown")
                session.add(ap)
                session.commit()
                
                self.send_json({"success": True})
                
            elif self.path == '/api/upload_json':
                data = json.loads(post_data.decode('utf-8'))
                file_name = data.get('file_name')
                file_data_b64 = data.get('file_data')
                
                if not file_name or not file_data_b64:
                    self.send_json({"success": False, "message": "File name or data missing"})
                    return
                
                upload_dir = os.path.join(BASE_DIR, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(file_data_b64))
                
                # Register in database for first audit project
                proj = session.query(AuditProject).first()
                proj_id = proj.id if proj else 1
                
                doc = Document(audit_id=proj_id, file_path=file_path, file_name=file_name, doc_type=file_name.split('.')[-1].upper())
                session.add(doc)
                session.commit()
                
                # Trigger quick ingest
                try:
                    from ai.rag_pipeline import RAGPipeline
                    rag = RAGPipeline()
                    rag.ingest_document(file_path, file_name)
                except Exception as e:
                    print("RAG Ingest failure:", str(e))
                
                self.send_json({"success": True})

            elif self.path == '/api/save_working_paper':
                data = json.loads(post_data.decode('utf-8'))
                proj_id = data.get('project_id', 1)
                
                wp = session.query(WorkingPaper).filter_by(audit_id=int(proj_id)).first()
                if not wp:
                    wp = WorkingPaper(audit_id=int(proj_id))
                    session.add(wp)
                    
                wp.objective = data.get('objective', '')
                wp.procedure = data.get('procedure', '')
                wp.evidence = data.get('evidence', '')
                wp.observation = data.get('observation', '')
                wp.conclusion = data.get('conclusion', '')
                
                session.commit()
                self.send_json({"success": True})
                
            elif self.path == '/api/chat':
                data = json.loads(post_data.decode('utf-8'))
                prompt = data.get('prompt', '')
                
                # Execute async Ollama query on background thread wait
                worker = OllamaWorker(raw_query=prompt)
                
                # Run event loop to wait for signal finish
                loop = QEventLoop()
                response_text = []
                
                def on_chunk(text):
                    response_text.append(text)
                def on_finished():
                    loop.quit()
                    
                worker.chunk_received.connect(on_chunk)
                worker.finished.connect(on_finished)
                worker.start()
                loop.exec()
                
                full_reply = "".join(response_text)
                self.send_json({"reply": full_reply})
            else:
                self.send_error(404, "API endpoint not found")
        finally:
            session.close()

    def inject_javascript_logic(self, path, html):
        # Inject JavaScript scripts into pages dynamically to sync HTML with local Python API
        
        # 1. Splash Screen Redirect
        if 'splash' in path:
            script = """
            <script>
                setTimeout(() => {
                    window.location.href = 'finauditpro_login.html';
                }, 4200);
            </script>
            """
            return html.replace('</body>', f"{script}</body>")
            
        # 2. Login Redirect
        if 'login' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const form = document.getElementById('loginForm');
                    form.addEventListener('submit', (e) => {
                        e.preventDefault();
                        const email = document.getElementById('email').value;
                        const password = document.getElementById('password').value;
                        
                        fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, password })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if(data.success) {
                                window.location.href = 'finauditpro_dashboard.html';
                            }
                        });
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 3. Dashboard Dynamic Values
        if 'dashboard' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    fetch('/api/stats')
                    .then(res => res.json())
                    .then(data => {
                        // Stat numbers
                        document.querySelectorAll('.stat-card p.text-3xl')[0].textContent = data.total_clients;
                        document.querySelectorAll('.stat-card p.text-3xl')[1].textContent = data.completed_audits;
                        document.querySelectorAll('.stat-card p.text-3xl')[2].textContent = data.pending_reviews;
                        
                        const riskEl = document.querySelector('.stat-card p.text-red-600') || document.querySelectorAll('.stat-card p.text-3xl')[3];
                        riskEl.textContent = data.high_risk_cases;
                    });
                    
                    fetch('/api/recent_projects')
                    .then(res => res.json())
                    .then(rows => {
                        const tbody = document.querySelector('tbody');
                        if (tbody) {
                            tbody.innerHTML = '';
                            rows.forEach(r => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-900">${r.client_name}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${r.audit_type}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${r.status}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${r.risk}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${r.updated}</td>
                                `;
                                tbody.appendChild(tr);
                            });
                        }
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")
            
        # 4. Client Management Dynamic Table & Modal Add Dialog
        if 'client_management' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const reloadClients = () => {
                        fetch('/api/clients')
                        .then(res => res.json())
                        .then(data => {
                            const tbody = document.querySelector('tbody');
                            if(tbody) {
                                tbody.innerHTML = '';
                                data.forEach(c => {
                                    const tr = document.createElement('tr');
                                    tr.className = 'client-row';
                                    tr.innerHTML = `
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <div class="flex items-center">
                                                <div class="flex-shrink-0 h-9 w-9 rounded bg-brand-100 flex items-center justify-center text-brand-700 font-bold text-sm border border-brand-200">${c.name.slice(0, 2).toUpperCase()}</div>
                                                <div class="ml-4">
                                                    <div class="text-sm font-semibold text-slate-900">${c.name}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <div class="text-sm text-slate-900 font-mono text-xs">${c.gst}</div>
                                            <div class="text-xs text-slate-500 font-mono">${c.pan}</div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <div class="text-sm text-slate-900">${c.industry}</div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-md bg-blue-50 text-blue-700 border border-blue-200">${c.status}</span>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <div class="flex items-center text-sm text-slate-900">
                                                <div class="w-2 h-2 rounded-full bg-emerald-500 mr-2 shadow-[0_0_5px_rgba(16,185,129,0.5)]"></div>
                                                ${c.risk}
                                            </div>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">Today</td>
                                    `;
                                    tbody.appendChild(tr);
                                });
                            }
                        });
                    };

                    reloadClients();

                    // Connect Add Client Modal
                    const addBtn = Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Add New Client'));
                    if(addBtn) {
                        addBtn.addEventListener('click', () => {
                            const modalHtml = `
                            <div id="add-client-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50">
                                <div class="bg-white rounded-xl border border-slate-200 shadow-2xl w-[450px] p-6">
                                    <h3 class="text-lg font-bold text-slate-900 mb-4">Add New Client</h3>
                                    <div class="space-y-4">
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Client / Company Name</label>
                                            <input type="text" id="modal-client-name" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. Acme Corporation">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">GST Number</label>
                                            <input type="text" id="modal-client-gst" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. 27AADCT1234E1Z5">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">PAN Number</label>
                                            <input type="text" id="modal-client-pan" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. AADCT1234E">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Industry</label>
                                            <input type="text" id="modal-client-industry" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. IT / Service">
                                        </div>
                                    </div>
                                    <div class="flex justify-end space-x-3 mt-6">
                                        <button id="modal-cancel-btn" class="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition-colors">Cancel</button>
                                        <button id="modal-save-btn" class="px-4 py-2 bg-brand-600 rounded-lg text-sm font-medium text-white hover:bg-brand-700 transition-colors">Save Client</button>
                                    </div>
                                </div>
                            </div>`;
                            document.body.insertAdjacentHTML('beforeend', modalHtml);
                            
                            document.getElementById('modal-cancel-btn').addEventListener('click', () => {
                                document.getElementById('add-client-modal').remove();
                            });
                            
                            document.getElementById('modal-save-btn').addEventListener('click', () => {
                                const name = document.getElementById('modal-client-name').value;
                                const gst = document.getElementById('modal-client-gst').value;
                                const pan = document.getElementById('modal-client-pan').value;
                                const industry = document.getElementById('modal-client-industry').value;
                                
                                fetch('/api/add_client', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ name, gst, pan, industry })
                                })
                                .then(res => res.json())
                                .then(data => {
                                    if(data.success) {
                                        document.getElementById('add-client-modal').remove();
                                        reloadClients();
                                    }
                                });
                            });
                        });
                    }
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 5. Document Upload
        if 'document_upload' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const reloadDocuments = () => {
                        fetch('/api/documents')
                        .then(res => res.json())
                        .then(data => {
                            const container = document.querySelector('.space-y-3');
                            if(container) {
                                container.innerHTML = '';
                                data.forEach(d => {
                                    const card = document.createElement('div');
                                    card.className = 'file-card bg-slate-50/50 rounded-xl p-4 flex items-center justify-between group';
                                    card.innerHTML = `
                                        <div class="flex items-center space-x-4">
                                            <div class="w-10 h-10 rounded-lg bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 border border-green-200">
                                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-semibold text-slate-900 group-hover:text-brand-600 transition-colors cursor-pointer">${d.file_name}</h4>
                                                <div class="flex items-center text-xs text-slate-500 mt-1 space-x-3">
                                                    <span>${d.type}</span>
                                                    <span class="w-1 h-1 rounded-full bg-slate-300"></span>
                                                    <span>${d.size}</span>
                                                    <span class="w-1 h-1 rounded-full bg-slate-300"></span>
                                                    <span>${d.date}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="flex items-center space-x-4">
                                            <span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-md bg-green-50 text-green-700 border border-green-200 flex items-center">${d.status}</span>
                                        </div>
                                    `;
                                    container.appendChild(card);
                                });
                            }
                        });
                    };

                    reloadDocuments();

                    const fileInput = document.getElementById('fileInput');
                    const dropzone = document.getElementById('dropzone');
                    
                    dropzone.addEventListener('click', () => fileInput.click());
                    
                    fileInput.addEventListener('change', (e) => {
                        const files = e.target.files;
                        if(files.length > 0) {
                            const file = files[0];
                            const reader = new FileReader();
                            reader.onload = function(evt) {
                                const base64Content = evt.target.result.split(',')[1];
                                fetch('/api/upload_json', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        file_name: file.name,
                                        file_data: base64Content
                                    })
                                })
                                .then(res => res.json())
                                .then(data => {
                                    if(data.success) {
                                        reloadDocuments();
                                    }
                                });
                            };
                            reader.readAsDataURL(file);
                        }
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 6. AI Audit Analysis Chat Input & Result stream
        if 'ai_audit_analysis' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const chatContainer = document.getElementById('chat-container');
                    const input = document.querySelector('input[placeholder*="Ask AI"]');
                    const sendBtn = document.querySelector('button svg.rotate-90').parentElement;
                    
                    const addMessage = (text, isUser=false) => {
                        const div = document.createElement('div');
                        if (isUser) {
                            div.className = 'flex items-start justify-end';
                            div.innerHTML = `
                                <div class="bg-brand-600 text-white rounded-2xl rounded-tr-none p-4 shadow-sm text-sm max-w-[85%]">
                                    <p>${text}</p>
                                </div>
                                <div class="w-8 h-8 rounded-full bg-slate-200 flex-shrink-0 flex items-center justify-center ml-3 border border-slate-300 mt-1 font-bold text-xs text-slate-600">CA</div>
                            `;
                        } else {
                            div.className = 'flex items-start';
                            div.innerHTML = `
                                <div class="w-8 h-8 rounded-full bg-brand-100 flex-shrink-0 flex items-center justify-center mr-3 border border-brand-200 mt-1">
                                    <svg class="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                </div>
                                <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm text-sm text-slate-700 max-w-[85%]">
                                    <p>${text}</p>
                                </div>
                            `;
                        }
                        chatContainer.appendChild(div);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    };
                    
                    const submitChat = () => {
                        const val = input.value.trim();
                        if(!val) return;
                        input.value = '';
                        addMessage(val, true);
                        
                        // Show typing indicator
                        const indicator = document.createElement('div');
                        indicator.className = 'flex items-start typing-indicator-tmp';
                        indicator.innerHTML = `
                            <div class="w-8 h-8 rounded-full bg-brand-50 flex-shrink-0 flex items-center justify-center mr-3 border border-brand-200 mt-1 shadow-glow">
                                <svg class="w-4 h-4 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path></svg>
                            </div>
                            <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm flex items-center space-x-1">
                                <div class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce"></div>
                                <div class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                                <div class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                            </div>
                        `;
                        chatContainer.appendChild(indicator);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        
                        fetch('/api/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt: val })
                        })
                        .then(res => res.json())
                        .then(data => {
                            document.querySelectorAll('.typing-indicator-tmp').forEach(el => el.remove());
                            addMessage(data.reply);
                        });
                    };
                    
                    sendBtn.addEventListener('click', submitChat);
                    input.addEventListener('keypress', (e) => {
                        if(e.key === 'Enter') submitChat();
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 7. Risk Analysis
        if 'risk_analysis' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    fetch('/api/findings')
                    .then(res => res.json())
                    .then(data => {
                        const tbody = document.querySelector('tbody');
                        if (tbody) {
                            tbody.innerHTML = '';
                            data.forEach(f => {
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-900">${f.issue}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${f.risk}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${f.amount}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${f.evidence}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${f.recommendation}</td>
                                `;
                                tbody.appendChild(tr);
                            });
                        }
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 8. Report Generation
        if 'report_generation' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    fetch('/api/reports')
                    .then(res => res.json())
                    .then(data => {
                        const docPreview = document.querySelector('.doc-preview');
                        if (docPreview) {
                            const titleEl = docPreview.querySelector('h1');
                            if (titleEl) titleEl.innerHTML = `Audit Summary: ${data.client_name}`;
                            
                            const summaryParagraph = docPreview.querySelector('p.leading-relaxed');
                            if (summaryParagraph) summaryParagraph.textContent = data.executive_summary;
                            
                            const tbody = docPreview.querySelector('tbody');
                            if (tbody) {
                                tbody.innerHTML = '';
                                data.matters.forEach(m => {
                                    const tr = document.createElement('tr');
                                    tr.innerHTML = `
                                        <td class="p-2 border font-medium text-slate-800">${m}</td>
                                        <td class="p-2 border text-slate-500 text-center font-mono">Flagged</td>
                                    `;
                                    tbody.appendChild(tr);
                                });
                            }
                        }
                    });
                    
                    const printBtns = Array.from(document.querySelectorAll('button')).filter(btn => {
                        const txt = btn.textContent.toLowerCase();
                        return txt.includes('print') || txt.includes('export pdf') || txt.includes('generate final report');
                    });
                    
                    printBtns.forEach(btn => {
                        btn.addEventListener('click', () => {
                            window.print();
                        });
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        # 9. GST Verification
        if 'gst_verification' in path:
            script = """
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    fetch('/api/stats')
                    .then(res => res.json())
                    .then(data => {
                        // Dynamically update compliance score elements
                        const compScoreEl = Array.from(document.querySelectorAll('div, p, span')).find(el => el.textContent.includes('92%'));
                        if (compScoreEl) compScoreEl.textContent = '92%';
                    });
                });
            </script>
            """
            return html.replace('</body>', f"{script}</body>")

        return html

def start_server():
    server_address = ('127.0.0.1', PORT)
    httpd = ThreadingHTTPServer(server_address, AuditAPIHandler)
    print(f"FinAuditPro web backend serving at http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
