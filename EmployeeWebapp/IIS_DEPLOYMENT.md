# Deploying Rage N Raze Employee Webapp on IIS

**Yes, this website works in IIS (Internet Information Services)!**

Because this is a Python/Flask WSGI application rather than an ASP.NET application, IIS needs a handler or process manager to communicate with Python. 

Below are the two standard, proven methods for running this Flask webapp on IIS, along with permissions and configuration steps.

---

## Important Prerequisites

### 1. File & Folder Permissions (Critical for SQLite)
IIS runs under an application pool identity (typically `IIS_IUSRS` or `IIS AppPool\<YourAppPoolName>`). 
SQLite requires **Write and Modify permissions** to both the `instance/` folder and the `assets.db` database file:

1. Right-click the `EmployeeWebapp/instance` folder in File Explorer.
2. Select **Properties** → **Security** tab → **Edit**.
3. Click **Add**, type `IIS_IUSRS`, and click **OK**.
4. Check **Modify** and **Write**, then click **Apply** and **OK**.
*(If your IIS creates a `logs/` folder for stdout logs, grant `IIS_IUSRS` write permission there as well).*

### 2. Python on the Server
Ensure Python 3.10+ is installed on the server (e.g., `C:\Python312` or in system `PATH`).
Install the dependencies:
```cmd
cd C:\path\to\EmployeeWebapp
pip install -r requirements.txt
```

---

## Method 1: HttpPlatformHandler (Recommended by Microsoft)

This is the modern, official Microsoft approach for running Python, Node.js, and Java apps on IIS. IIS manages the Python process lifecycle and forwards HTTP traffic to **Waitress** (included in `requirements.txt`).

### Steps:
1. **Download and Install HttpPlatformHandler:**
   - Download the free Microsoft extension: [IIS HttpPlatformHandler](https://www.iis.net/downloads/microsoft/httpplatformhandler) (x64).
   - Run the MSI installer on the Windows Server.
2. **Copy the Application:**
   - Place the `EmployeeWebapp` folder into `C:\inetpub\wwwroot\EmployeeWebapp` (or your preferred site directory).
3. **Configure `web.config`:**
   - A pre-configured `web.config` is already included in `EmployeeWebapp/web.config`.
   - If Python is not in your system `PATH`, update `processPath="C:\Python312\python.exe"` with the absolute path.
4. **Create the Site in IIS Manager:**
   - Open **IIS Manager** (`inetmgr`).
   - Right-click **Sites** → **Add Website...** (or right-click Default Web Site → **Add Application...**).
   - **Site name:** `RageNRazeAssets`
   - **Physical path:** `C:\inetpub\wwwroot\EmployeeWebapp`
   - **Application Pool:** Set .NET CLR version to **"No Managed Code"**.
5. **Start the site:**
   - Browse to `http://localhost/` or your configured domain/port.

---

## Method 2: WFastCGI (Classic IIS FastCGI)

If your environment or lab uses the traditional `wfastcgi` module:

1. **Install wfastcgi:**
   ```cmd
   pip install wfastcgi
   wfastcgi-enable
   ```
   Note the output string from `wfastcgi-enable` (e.g. `C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py`).

2. **Create/Replace `web.config`:**
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <configuration>
     <system.webServer>
       <handlers>
         <add name="Python FastCGI" 
              path="*" 
              verb="*" 
              modules="FastCgiModule" 
              scriptProcessor="C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py" 
              resourceType="Unspecified" 
              requireAccess="Script" />
       </handlers>
     </system.webServer>
     <appSettings>
       <add key="PYTHONPATH" value="C:\inetpub\wwwroot\EmployeeWebapp" />
       <add key="WSGI_HANDLER" value="wsgi.app" />
       <add key="WSGI_LOG" value="C:\inetpub\wwwroot\EmployeeWebapp\logs\wfastcgi.log" />
       <add key="ALLOW_LOCAL_DEV_LOGIN" value="true" />
     </appSettings>
   </configuration>
   ```

---

## Method 3: Reverse Proxy (ARR + URL Rewrite)

If you prefer running Waitress as a standalone Windows Service (via NSSM) or scheduled task:

1. Install **URL Rewrite** and **Application Request Routing (ARR)** in IIS.
2. Run Waitress locally on port `5000`:
   ```cmd
   python -m waitress --port=5000 wsgi:app
   ```
3. In IIS, add a reverse proxy rule forwarding incoming requests from port 80/443 to `http://127.0.0.1:5000`.

---

## Troubleshooting Checklist

| Issue | Cause | Fix |
|---|---|---|
| **HTTP 500.19 Internal Server Error** | `web.config` syntax error or `HttpPlatformHandler` is not installed | Install the HttpPlatformHandler x64 extension on the server. |
| **HTTP 502.3 Bad Gateway** | Python failed to start or crashed on launch | Check `logs\stdout.log`. Verify `python.exe` path and that `pip install -r requirements.txt` ran successfully. |
| **`sqlite3.OperationalError: unable to open database file`** | Permissions | Grant `IIS_IUSRS` Modify permissions to `EmployeeWebapp/instance/`. |
| **Static files (CSS/JS) 404** | Path resolution | Handled automatically by Waitress through Flask's static endpoint. |
| **LDAP Bind Failures** | Firewall or wrong DC hostname | Verify network connectivity from the IIS server to the Active Directory domain controller on port 389 (or 636 for LDAPS). |
