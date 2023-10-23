import subprocess

# Step 1: Install Apache 2.4
subprocess.run(["sudo", "apt-get", "update"])
subprocess.run(["sudo", "apt-get", "install", "apache2"])

# Step 2: Create Directories
subprocess.run(["sudo", "mkdir", "/var/www/logData"])
subprocess.run(["sudo", "mkdir", "/var/www/credentialList"])

# Step 3: Set Permissions
subprocess.run(["sudo", "chown", "-R", "www-data:www-data", "/var/www/logData"])
subprocess.run(["sudo", "chown", "-R", "www-data:www-data", "/var/www/credentialList"])

# Step 4: Configure Apache
apache_config = """
DocumentRoot /var/www
<Directory /var/www/logData>
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
<Directory /var/www/credentialList>
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
"""

# Add the Apache configuration to the default site
with open("/etc/apache2/sites-available/000-default.conf", "a") as apache_conf_file:
    apache_conf_file.write(apache_config)

# Step 5: Enable the Site and Reload Apache
subprocess.run(["sudo", "a2ensite", "000-default.conf"])
subprocess.run(["sudo", "systemctl", "reload", "apache2"])

print("Apache 2.4 has been configured with 'logData' and 'credentialList' directories.")
