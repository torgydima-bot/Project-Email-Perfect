import sqlite3

DB = '/var/www/email-perfect/email_perfect.db'
conn = sqlite3.connect(DB)

# Add contact_name column
try:
    conn.execute("ALTER TABLE campaign_logs ADD COLUMN contact_name VARCHAR(200) DEFAULT ''")
    conn.commit()
    print('contact_name column added')
except Exception as e:
    print('exists:', e)

# Add gender column to contacts
try:
    conn.execute("ALTER TABLE contacts ADD COLUMN gender VARCHAR(1) DEFAULT ''")
    conn.commit()
    print('gender column added')
except Exception as e:
    print('exists:', e)

# Reset test contact names
for email in ['torgydima@gmail.com', 'sdv201854@mail.ru', 'vds36@yandex.ru']:
    conn.execute("UPDATE contacts SET first_name='', last_name='' WHERE email=?", (email,))
conn.commit()
print('names reset')

conn.close()
