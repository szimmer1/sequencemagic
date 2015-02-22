# -*- coding: utf-8 -*-
from datetime import datetime

"""
Define get_first_name function for finding users names,
as well as define table of users.
"""

def get_first_name():
   name = ''
   if auth.user:
      name = auth.user.first_name
   return name

db.define_table('users',
				Field('name'), 
                Field('user_id', db.auth_user),
                Field('email'),
                )

db.users.name.default = get_first_name()
db.users.email.requires = IS_EMAIL()

"""
descriptor table, which contains all seqID's related to
a specific user. A user may have many different sequences, with 
many different annotations per sequence.
"""
db.define_table('descriptor_table',
				Field('seqID'),
				Field('user_id' , 'reference users')
				)
				
"""
sequence table, which contain all the sequences
a user has chosen to enter.

This should be able to accept FASTA files and strip them
down to plain text. Shouldn't be too big of a deal to
implement.
"""
db.define_table('sequences',
				Field('seq', 'text'),
				Field('descriptor_id' , 'reference descriptor_table'),
				Field('date_created', 'datetime')
				)
				
"""
annotations table. This is the list of substrings and their identifier
sequence.
"""
db.define_table('annotations',
				 Field('annotation_name'),
				 Field('annotation_location'),
				 Field('descriptor_id' , 'reference descriptor_table'),
				 Field('date_created', 'datetime'),
				 Field('annotation_description', 'text')
				 )
				 
"""Here is a FASTA reader method that we may need in a controller.
I used this for my BME 160 class so it will probably have to do be modified
but it doesn't hurt to have as reference
with open(self.fname) as fileH:
   header=''
   sequence=''
   
   line = fileH.readline()
   while not line.startswith('>'):
      line = fileH.readline()
   header = line[1:].rstrip()
   for line in fileH:
      if line.startswith('>'):
         yield header,sequence
         header = line[1:].rstrip()
         sequence = ''
      else:
         sequence += ''.join(line.rstrip().split()).upper()
      yield header, sequence
"""