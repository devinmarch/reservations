For my own information, I want to create a microservice where the core functionality is to create or delete based on room_block webhooks with some filtering.

We'll use a new table called RoomBlockCode.

When a webhook is received that a new out_of_service roomblock is created with the description "hairycat", we'll use the the Lock table to look up the lock with the room_id, install a code using the start and end date, and write the code to the new table with the seam id and room_block_id. Well then call cloudbeds with putRoomBlock append the description using roomBlockReason with Code: + the code seam generated.

### Sample payload
{ "version": "1.0", "roomBlockID": "169266429834303645", "propertyID": 12345, "roomBlockType": "out_of_service", "roomBlockReason": "test", "startDate": "2023-08-28", "endDate": "2023-08-30", "rooms": [ { "roomID": "445566-1", "roomTypeID": 445566 } ], "event": "roomblock/created", "timestamp": 1611758157.431234}

When a webhook is received that that a payload is deleted, look up the roomblock id in the table, delete the seam code, and delete the record.