# -*- coding: utf-8 -*-
from datetime import datetime
import os

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
   parseSequence(form.vars.file_type,form.vars.sequence_file, seq_id)
   return dict(desc_id = desc_id, seq_id=seq_id)

def update_existing_sequence(form,flag):
    existing_desc_row = db(db.descriptor_table.sequence_name == form.vars.name).select().first().seq_id
    existing_seq_row = db(db.sequences.id == existing_desc_row).select().first()
    existing_seq = existing_seq_row.seq
    # make list of ints because form.vars.position is a string
    position_list = []
    test_list = form.vars.position.replace(',',' ').replace('-',' ').split()
    for pos in test_list:
        position_list.append(int(pos))

    #redirect(URL('default', 'index', vars=dict(position_list=test_list)))

    if flag == 'del': # only allowing for a single base, one substring of bases, or multiple substrings
        new_seq = ''
        # redirect(URL('default', 'index', vars=dict(pos=position_list[0])))
        if len(position_list) == 1: # deleting single base
            if position_list[0] <= 0: # delete first base
                new_seq = existing_seq[1:]
            elif position_list[0] > len(existing_seq): # delete last base
                # redirect(URL('default', 'index', vars=dict(pos=position_list[0])))
                new_seq = existing_seq[0:-1]
            else:
                new_seq = existing_seq[0:position_list[0]]
                new_seq += existing_seq[position_list[0]+1:]
        elif len(position_list) % 2 == 0: # deleting at least one substring
            seqs_to_del = []
            new_seq = existing_seq
            for pos in range(0, len(position_list),2): # first get all instances of string
                pos1 = position_list[pos]
                pos2 = position_list[pos+1]
                del_seq = existing_seq[pos1:pos2+1]
                seqs_to_del.append(del_seq)
            for seq in seqs_to_del: # now replace by empty string
                new_seq = new_seq.replace(seq,'',1)
        existing_seq_row.update_record(seq=new_seq)

    elif flag == 'add': # inserts to the left of user selected position(s)
        new_seq = ''
        if len(position_list) == 1: # adding in sequence in only one position
            if position_list[0] <= 0: # prepend
                new_seq = form.vars.seqs + existing_seq
            elif position_list[0] > len(existing_seq): # append
                new_seq = existing_seq + form.vars.seqs
            else: # insert new sequence to left of user selected position
                new_seq = existing_seq[0:position_list[0]]
                new_seq += form.vars.seqs
                new_seq += existing_seq[position_list[0]:]
            existing_seq_row.update_record(seq=new_seq)
        elif len(position_list) > 1: # adding left of more than one position
            for pos in range(0, len(position_list), 1):
                updated_row = db(db.sequences.id == existing_desc_row).select().first()
                updated_seq = updated_row.seq
                if position_list[pos] > len(existing_seq):
                    updated_seq += form.vars.seqs
                    updated_row.update_record(seq=updated_seq)
                else:
                    new_seq = updated_seq[:position_list[pos]]
                    new_seq += form.vars.seqs
                    new_seq += existing_seq[position_list[pos]:]
                    updated_row.update_record(seq=new_seq)

    elif flag == 'replace': # replaces user specified substring with user input seq
        new_seq = ''
        if len(position_list) == 1: # adding in sequence in only one position
            if position_list[0] <= 0: # prepend
                new_seq = form.vars.seqs + existing_seq
            elif position_list[0] > len(existing_seq): # replace last base
                new_seq = existing_seq[:len(existing_seq)-1] + form.vars.seqs
            else: # change one base
                new_seq = existing_seq[:position_list[0]] + form.vars.seqs + existing_seq[position_list[0]+1:]
            existing_seq_row.update_record(seq=new_seq)
        elif len(position_list) % 2 == 0:
            seqs_to_del = []
            new_seq = existing_seq
            for pos in range(0, len(position_list),2): # first get all instances of string
                pos1 = position_list[pos]
                pos2 = position_list[pos+1]
                del_seq = existing_seq[pos1:pos2+1]
                seqs_to_del.append(del_seq)
            for seq in seqs_to_del: # now replace by empty string
                new_seq = new_seq.replace(seq,form.vars.seqs,1)
        existing_seq_row.update_record(seq=new_seq)

def insert_descriptor_table(form, seq_id):
   # updates descriptor_table table with sequence name, description, and id
   descriptor_id = db.descriptor_table.insert(seq_id = seq_id,
                              sequence_name = form.vars.name,
                              sequence_description = form.vars.description,
                              date_created = datetime.utcnow()
                             )
   
   return descriptor_id
   
def update_descriptor_to_user(desc_id):
   #if db.descriptor_to_user.description_id
   db.descriptor_to_user.insert(descriptor_id = desc_id)

def insert_annotation(form):
   annotation_id = db.annotations.insert(annotation_name = form.vars.annotation_name,
                              annotation_location = form.vars.annotation_position,
                              date_created = datetime.utcnow(),
                              annotation_description = form.vars.description,
                              annotation_length = form.vars.length
                              )
   descriptor_id = db(db.descriptor_table.sequence_name == form.vars.seq_name).select().first().id
   update_annotation_to_descriptor(annotation_id, descriptor_id)
   annotation_name = form.vars.annotation_name
   update_active_annotations(annotation_id,annotation_name , descriptor_id)
   return descriptor_id

def update_annotation_to_descriptor(annotation_id, descriptor_id):
   db.annotation_to_descriptor.insert(annotation_id = annotation_id, descriptor_id = descriptor_id)

def update_active_annotations(new_id, new_name, desc_id):
	item = db((db.active_annotations.annotation_name==new_name) & (
		db.active_annotations.descriptor_id == desc_id)).select().first()
	if item:	
		db((db.active_annotations.annotation_name==new_name) &(
			db.active_annotations.descriptor_id == desc_id)).update(active_id=new_id)
	else:
		db.active_annotations.insert(active_id = new_id, 
									annotation_name = new_name,
									descriptor_id = desc_id
									)

def parseSequence(filetype, filename, seq_id):
	SEQFILE = open(os.path.join(request.folder+'static/uploads/'+filename))

	if filetype == FASTA:
		sequence = ''
		firstseq = False
		for line in SEQFILE:
			if line.startswith('>'):
				if firstseq: break
				firstseq = True
			else:
				sequence += line.strip()
		db(db.sequences.id==seq_id).update(seq = sequence)


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
				 Field('annotation_location', 'list:integer'),
				 Field('date_created', 'datetime'),
				 Field('annotation_description', 'text'),
                 Field('annotation_length', 'integer'),
				 Field('creating_user_id', 'reference auth_user'),
				 )
db.annotations.creating_user_id.default = auth.user_id

'''
active_annotations
creates an index for each unique annotation name.
Used to generate annotation groups for versioning
'''
db.define_table('active_annotations',
				Field('annotation_name'),
				Field('active_id', 'reference annotations'),
				Field('descriptor_id', 'reference descriptor_table'),
                fake_migrate=True
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
