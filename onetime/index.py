from mods.firemod import init_db, FieldFilter, Or, And

db = init_db()
print(db.collection('Task').where(FieldFilter('name_task', '==', 'Change oil')).where(filter=Or([
            FieldFilter('status', '==', True),
            And([
                FieldFilter('status', '==', False),
                FieldFilter('post', '==', True)
            ])
        ])).get())