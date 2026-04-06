import os
import json
import glob
import webbrowser

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, 'logs')
    report_dir = os.path.join(base_dir, 'report')
    
    all_logs = []
    # Read all log files
    for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_logs.append(json.loads(line))
                    except:
                        pass
                        
    # Sort logs by timestamp just in case
    all_logs.sort(key=lambda x: x.get('timestamp', ''))
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Agent Telemetry Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        body { 
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); 
            color: #fff; 
            min-height: 100vh; 
            padding: 2rem; 
        }
        .glass-panel { 
            background: rgba(255, 255, 255, 0.08); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border-radius: 16px; 
            padding: 24px; 
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1); 
            border: 1px solid rgba(255, 255, 255, 0.2); 
            margin-bottom: 24px; 
            overflow: hidden;
            animation: fadeIn 0.5s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 { 
            font-weight: 800; 
            font-size: 2.5rem; 
            margin-top: 0; 
            text-align: center; 
            text-transform: uppercase; 
            letter-spacing: 2px; 
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .summary-cards {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .card:hover { transform: scale(1.05); }
        .card-val { font-size: 2rem; font-weight: 800; margin-bottom: 5px; color: #06d6a0; }
        .card-label { font-size: 0.9rem; text-transform: uppercase; color: #a8b2d1; letter-spacing: 1px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; text-align: left; table-layout: fixed;}
        th, td { padding: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); vertical-align: top;}
        th { font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; color: #a8b2d1; }
        tr:hover { background: rgba(255, 255, 255, 0.05); }
        
        .col-time { width: 150px; }
        .col-event { width: 180px; }
        .col-data { width: auto; }
        
        .event-badge { 
            padding: 6px 12px; 
            border-radius: 8px; 
            font-size: 0.85rem; 
            font-weight: 800; 
            display: inline-block;
            text-transform: uppercase;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .event-LLM_METRIC { background: linear-gradient(135deg, #118ab2, #073b4c); color: white;}
        .event-AGENT_START { background: linear-gradient(135deg, #06d6a0, #04a57b); color: #111; }
        .event-AGENT_STEP { background: linear-gradient(135deg, #ffd166, #ffb703); color: #111; }
        .event-AGENT_END { background: linear-gradient(135deg, #ef476f, #ae2012); color: white; }
        .event-AGENT_GUARDRAIL { background: linear-gradient(135deg, #9d4edd, #5a189a); color: white; }
        .event-CHATBOT_RESPONSE { background: linear-gradient(135deg, #48cae4, #0077b6); color: white; }
        
        .data-pre { 
            background: rgba(0,0,0,0.4); 
            padding: 12px; 
            border-radius: 8px; 
            font-size: 0.85rem; 
            white-space: pre-wrap; 
            word-wrap: break-word;
            margin: 0;
            border: 1px solid rgba(255,255,255,0.05);
            font-family: 'Consolas', monospace;
            color: #e2e8f0;
        }
        
        /* Specific highlight for thought/action text */
        .highlight-key { color: #f4a261; font-weight: bold; }
        .highlight-val { color: #2a9d8f; }
        .highlight-str { color: #e9c46a; }
    </style>
</head>
<body>
    <h1>🚀 Telemetry Dashboard</h1>
    
    <div class="summary-cards">
        <div class="card">
            <div class="card-val" id="total-events">0</div>
            <div class="card-label">Total Events</div>
        </div>
        <div class="card">
            <div class="card-val" id="total-cost">$0.000</div>
            <div class="card-label">Est. Cost</div>
        </div>
        <div class="card">
            <div class="card-val" id="total-latency">0ms</div>
            <div class="card-label">Total LLM Latency</div>
        </div>
    </div>

    <div class="glass-panel">
        <table>
            <thead>
                <tr>
                    <th class="col-time">Time</th>
                    <th class="col-event">Event</th>
                    <th class="col-data">Payload / Content</th>
                </tr>
            </thead>
            <tbody id="table-body">
            </tbody>
        </table>
    </div>

    <script>
        const logs = __LOG_DATA__;
        
        // Calculate Metrics
        let totalCost = 0.0;
        let totalLatency = 0;
        
        logs.forEach(log => {
            if(log.event === 'LLM_METRIC' && log.data) {
                totalCost += (log.data.cost_estimate || 0);
                totalLatency += (log.data.latency_ms || 0);
            }
        });
        
        document.getElementById('total-events').innerText = logs.length;
        document.getElementById('total-cost').innerText = '$' + totalCost.toFixed(4);
        document.getElementById('total-latency').innerText = totalLatency + 'ms';
        
        // Render Table
        const tbody = document.getElementById('table-body');
        logs.forEach(log => {
            const tr = document.createElement('tr');
            
            // Format time
            const timeStr = log.timestamp ? log.timestamp.split('T')[1].substring(0, 12) : '';
            
            // Format JSON data with light syntax highlighting for string display
            let displayData = JSON.parse(JSON.stringify(log.data || {}));
            
            // Xóa phần reasoning (Thought)
            if (log.event === 'AGENT_STEP' && displayData.llm_output) {
                displayData.llm_output = displayData.llm_output.replace(/Thought:[\s\S]*?(?=Action:|Final Answer:|$)/i, '').trim();
            }
            
            let dataStr = JSON.stringify(displayData, null, 2) || '';
            // Basic regex to wrap strings and keys
            dataStr = dataStr.replace(/"([^"]+)":/g, '<span class="highlight-key">"$1"</span>:')
                             .replace(/"([^"]+)"(?=[,\n\r}])/g, '<span class="highlight-str">"$1"</span>');
                             
            tr.innerHTML = `
                <td>${timeStr}</td>
                <td><span class="event-badge event-${log.event}">${log.event}</span></td>
                <td><div class="data-pre">${dataStr}</div></td>
            `;
            tbody.appendChild(tr);
        });
    </script>
</body>
</html>"""
    
    html_content = html_template.replace('__LOG_DATA__', json.dumps(all_logs))
    
    os.makedirs(report_dir, exist_ok=True)
    out_file = os.path.join(report_dir, 'log_viewer.html')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Generated UI Dashboard at: {out_file}")
    
    # Try to open automatically
    try:
        webbrowser.open(f"file://{out_file}")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == '__main__':
    main()
