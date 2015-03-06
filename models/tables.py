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
   
def insert_man_sequence(form):
   seq_id = db.sequences.insert(seq = form.vars.seqs)
   desc_id = insert_descriptor_table(form, seq_id)
   update_descriptor_to_user(desc_id)
   return dict(desc_id=desc_id, seq_id=seq_id)

def insert_file_sequence(form):
   seq_id = db.sequences.insert(
                     seq_file_name = form.vars.sequence_file, 
                     seq_file_type = form.vars.file_type
                     )
   desc_id = insert_descriptor_table(form, seq_id)
   update_descriptor_to_user(desc_id)
   return dict(desc_id = desc_id, seq_id=seq_id)



def insert_descriptor_table(form, seq_id):
   # updates descriptor_table table with sequence name, description, and id
   descriptor_id = db.descriptor_table.insert(seq_id = seq_id,
                              sequence_name = form.vars.name,
                              sequence_description = form.vars.description,
                              date_created = datetime.utcnow()
                             )
   
   return descriptor_id
   
def update_descriptor_to_user(desc_id):
   db.descriptor_to_user.insert(descriptor_id = desc_id)

def insert_annotation(form):
   annotation_id = db.annotations.insert(annotation_name = form.vars.annotation_name,
                              annotation_location = form.vars.annotation_position,
                              date_created = datetime.utcnow(),
                              annotation_description = form.vars.description,
                              )
   descriptor_id = db(db.descriptor_table.sequence_name == form.vars.seq_name).select().first().id
   update_annotation_to_descriptor(annotation_id, descriptor_id)
   return descriptor_id

def update_annotation_to_descriptor(annotation_id, descriptor_id):
   db.annotation_to_descriptor.insert(annotation_id = annotation_id, descriptor_id = descriptor_id)

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
				Field('seq_file_name', 'text'),
				Field('seq_file_type', 'text')
				# Field('descriptor_id' , 'reference descriptor_table'),
				)

"""
descriptor table, which contains all seqID's related to
a specific user. A user may have many different sequences, with 
many different annotations per sequence.
"""
db.define_table('descriptor_table',
                Field('seq_id', 'reference sequences'),
                Field('sequence_name'),
                Field('sequence_description', 'text'),
                Field('creating_user_id', 'reference auth_user'),
                Field('date_created', 'datetime')
				   )

db.descriptor_table.creating_user_id.default = auth.user_id

"""Linker table for descriptors and users"""
db.define_table('descriptor_to_user',
                Field('user_id', db.auth_user),
                Field('descriptor_id', 'reference descriptor_table')
                )

db.descriptor_to_user.user_id.default = auth.user_id


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
