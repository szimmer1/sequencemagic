
''' 
delete annotation will delete an annotation based on its annotation_id
''' 
def delete_annotation(annotation_id):
    desc_id = db(db.active_annotations.active_id==annotation_id).select().first().descriptor_id
    db(db.active_annotations.active_id==annotation_id).delete()
    db(db.annotation_to_descriptor.annotation_id==annotation_id).delete()
    db(db.annotations.id==annotation_id).delete()
    redirect(URL('default', 'view', args=[desc_id]))

 '''
delete_anntation_by_loc will delete all annotations on a given sequence
determined by localization over a region spanning index1 and index2
'''   
def delete_annotation_by_loc(descriptor_id, index1, index2):
    annotations = db(db.annotation_to_descriptor.descriptor_id==descriptor_id).select()
    for annotation in annotations:
        annot_id = annotation.id
        annot_index1 = annotation.annotation_location
        annot_index2 = annot_index1 + annotation.annotation_length
        if  (annot_index1==index1) or (annot_index2==index2) or (
                (annot_index1<index1) and (annot_index2>index2)):
            db(db.annotation_to_descriptor.annotation_id==annot_id).delete()
            db(db.active_annotations.active_id==annot_id).delete()
            db(db.annotations.id==annot_id).delete()
    redirect(URL('default', 'view', args=[descriptor_id]))

'''
delete_sequence will delete everything associated wit a sequence in the db
sequences, file uploads, annotations
'''    
def delete_sequence(descriptor_id):
    #delete discriptor_to_user typles
    db(db.descriptor_to_user.descriptor_id==descriptor_id).delete()
    #delete sequences tuple
    seq_id = db(db.descriptor_table.id==descriptor_id).select().first().seq_id
    seq_file_name = db(db.sequences.id==seq_id).select().first().seq_file_name
    db(db.sequences.id==seq_id).delete
    #remove uploaded file
    if seq_file_name <> None:
        os.remove(request.folder+'static/uploads/'+seq_file_name)
    #delete descriptor
    db(db.descriptor_table.id==descriptor_id).delete()
    #delete active_annotation tuple
    db(db.active_annotations.descriptor_id==descriptor_id).delete()
    #delete annotation tuples
    annotations = db(db.annotation_to_descriptor.descriptor_id==descriptor_id).select()
    for item in annotations:
        annot_id = item.annotation_id
        db(db.annotations.annotation_id==annot_id).delete()
        #delete annotation to descriptor tuples
        db(db.annotation_to_descriptor.annotation_id==annot_id).delete()

    redirect(URL('default', 'index', args=[auth.user_id]))

    
