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
   
def insert_sequence(form):
   seq_id = db.sequences.insert(seq = form.seq)
   desc_id = insert_descriptor_table(form, seq_id)
   # db(db.sequences.id==seq_id).update(descriptor_id = desc_id)
   update_descriptor_to_user(form, desc_id)

def insert_descriptor_table(form, seq_id):
   # updates descriptor_table table with sequence name, description, and id
   descriptor_id = db.descriptor_table.insert(seq_ID = db(db.sequences.id == seq_id).select(),
                              sequence_Name = form.name,
                              sequence_description = form.description,
                              date_created = datetime.utcnow()
                             )
   return descriptor_id
   
def update_descriptor_to_user(form, desc_id):
   db.descriptor_to_user.insert(user_id = db.auth_user,
                                descriptor_id = desc_id)

def update_annotation(form):
   pass


# db.users.name.default = get_first_name()
# db.users.email.requires = IS_EMAIL()
"""
sequence table, which contain all the sequences
a user has chosen to enter.

This should be able to accept FASTA files and strip them
down to plain text. Shouldn't be too big of a deal to
implement.
"""
db.define_table('sequences',
				Field('seq', 'text'),
				# Field('descriptor_id' , 'reference descriptor_table'),
				)

"""
descriptor table, which contains all seqID's related to
a specific user. A user may have many different sequences, with 
many different annotations per sequence.
"""
db.define_table('descriptor_table',
                Field('seq_ID', 'reference sequences'),
                Field('sequence_Name'),
                Field('sequence_description' , 'text'),
                Field('date_created', 'datetime')
				   )

"""Linker table for descriptors and users"""
db.define_table('descriptor_to_user',
                Field('user_id', db.auth_user),
                Field('descriptor_id', 'reference descriptor_table')
                )

db.descriptor_to_user.default = auth.user_id


				
"""
annotations table. This is the list of substrings and their identifier
sequence.
"""
db.define_table('annotations',
				 Field('annotation_name'),
				 Field('annotation_location' , 'list:integer'),
				 Field('date_created', 'datetime'),
				 Field('annotation_description', 'text')
				 )

"""Linker table for annotations and descriptors"""
db.define_table('annotation_to_descriptor',
                Field('descriptor_id', 'reference descriptor_table'),
                Field('annotation_id', 'reference annotations')
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