import subprocess
import sqlite3
import os
import requests
import re
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

def add_ip_block(ip):
    """Add an IP block using iptables."""
    command = f"iptables -A INPUT -s {ip} -j DROP"
    subprocess.run(command, shell=True, check=True)

def remove_ip_block(ip):
    """Remove an IP block using iptables."""
    command = f"iptables -D INPUT -s {ip} -j DROP"
    subprocess.run(command, shell=True, check=True)

def log_firewall_action(ip, action):
    """Log a firewall action in the database."""
    conn = sqlite3.connect("firewall.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO firewall_logs (ip, action) VALUES (?, ?)", (ip, action)
    )
    conn.commit()
    conn.close()

def fetch_firewall_logs():
    """Fetch all firewall logs from the database."""
    conn = sqlite3.connect("firewall.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM firewall_logs")
    logs = cursor.fetchall()
    conn.close()
    return logs


load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

class Firewall:
    def __init__(self):
        self.log_file = "/var/log/firewall/firewall.log"
        self.ip_list_file = "/var/log/firewall/firewall_blocked.txt"
        self.whitelist_file = "/var/log/firewall/whitelist.txt"
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.pattern = re.compile(r"(\d{1,3}\.){3}\d{1,3}")
        self.init_firewall()
        self.setup_ipset()

    def run_commands(self, commands):
        """Executes multiple shell commands in sequence."""
        results = []
        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    check=True,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                output = result.stdout.decode("utf-8")
                time.sleep(0.1)  # Prevent race conditions
                logging.info(f"Command executed: {command}")
                results.append(output)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode("utf-8")
                logging.error(f"Command '{command}' failed: {error_msg}")
                results.append(f"Error: {error_msg}")
        return results

    def init_firewall(self):
        """Initializes the firewall with default rules."""
        commands = [
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "iptables -A INPUT -i lo -j ACCEPT",
        ]
        # Add port allowance
        for port in [53, 323, 10169, 67, 68, 80, 443]:
            commands.append(f"iptables -A INPUT -p tcp --dport {port} -j ACCEPT")
        self.run_commands(commands)

    def setup_ipset(self):
        """Sets up the ipset for efficient IP blocking."""
        commands = [
            "ipset create blacklist hash:ip",
            "iptables -I INPUT -m set --match-set blacklist src -j DROP",
        ]
        self.run_commands(commands)

    def add_tcp_scan_protection(self):
        """Adds protection against TCP scans."""
        commands = [
            "iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags ALL SYN,FIN,PSH,URG -j DROP",
            "iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST, SYN-RECV -j DROP",
        ]
        self.run_commands(commands)

    def add_flood_protections(self):
        """Adds protection against SYN Flood, HTTP Flood, etc."""
        commands = [
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            "iptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 20 -j DROP",
            "iptables -A INPUT -p tcp -m conntrack --ctstate NEW -m limit --limit 1/s --limit-burst 3 -j ACCEPT",
            "iptables -A INPUT -p tcp -m conntrack --ctstate NEW -j DROP",
            "iptables -A INPUT -m conntrack --ctstate INVALID -j DROP",
            "iptables -A INPUT -p tcp --syn -m connlimit --connlimit-above 10/s -j REJECT --reject-with tcp-reset",
        ]
        self.run_commands(commands)

    def add_ack_flood_protection(self):
        """Adds protection against ACK Flood attacks."""
        commands = [
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -m limit --limit 5/s --limit-burst 10 -j ACCEPT",
            "iptables -A INPUT -p tcp --tcp-flags ALL ACK -j DROP",
        ]
        self.run_commands(commands)

    def add_icmp_protection(self):
        """Adds protection against ICMP Flood attacks."""
        commands = [
            "iptables -A INPUT -p icmp -m limit --limit 1/s --limit-burst 5 -j ACCEPT",
            "iptables -A INPUT -p icmp -j DROP",
            "iptables -A INPUT -f -j DROP",
            "iptables -A INPUT -m state --state INVALID -j DROP",
        ]
        self.run_commands(commands)

    def enhanced_logging(self):
        """Enables enhanced logging for blocked packets."""
        command = "iptables -A INPUT -j LOG --log-prefix 'Blocked Input: ' --log-level 4"
        self.run_commands([command])


def init_firewall():
    firewall = Firewall()

    firewall.init_firewall()
    firewall.add_tcp_scan_protection()
    firewall.add_flood_protections()
    firewall.add_ack_flood_protection()
    firewall.add_icmp_protection()
    firewall.enhanced_logging()
