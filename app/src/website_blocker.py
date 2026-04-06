import platform

class HostsBlocker:
    def __init__(self):
        #detect the os to find the correct hosts file
        #ONLY TESTED ON WINDOWS SO FAR
        if platform.system() == 'Windows':
            self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        else:
            self.hosts_path = "/etc/hosts" 
        self.redirect_ip = "127.0.0.1"

    def start(self, websites_to_block):
        #adds blocked sites to hosts file
        if not websites_to_block:
            return True
        try:
            with open(self.hosts_path, 'r+') as file:
                content = file.read()
                for website in websites_to_block:
                    #blocks both www and normal version of site
                    sites = [website, f"www.{website}"]
                    for site in sites:
                        if f"{self.redirect_ip} {site}" not in content:
                            file.write(f"\n{self.redirect_ip} {site}\n")    
            print(f"[Blocker] Network block activated for: {websites_to_block}")
            return True
        except PermissionError:
            print("[Blocker] ERROR: Permission Denied. You must run this app as Administrator!")
            return False

    def stop(self, websites_to_block):
        #removes blocked site from hosts file
        if not websites_to_block:
            return True 
        try:
            with open(self.hosts_path, 'r+') as file:
                lines = file.readlines()
                file.seek(0)
                for line in lines:
                    #if line doesn't contain blocked sites, write it back
                    if not any(website in line for website in websites_to_block):
                        file.write(line)
                file.truncate()   
            print("[Blocker] Network block deactivated. Sites restored.")
            return True 
        except PermissionError:
            print("[Blocker] ERROR: Permission Denied. Cannot unblock sites.")
            return False