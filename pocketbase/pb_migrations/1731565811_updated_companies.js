/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("kaszjfi1uzdfexg")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "iyqdmgpk",
    "name": "attachments",
    "type": "file",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "mimeTypes": [],
      "thumbs": [],
      "maxSelect": 99,
      "maxSize": 5242880,
      "protected": false
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("kaszjfi1uzdfexg")

  // remove
  collection.schema.removeField("iyqdmgpk")

  return dao.saveCollection(collection)
})
