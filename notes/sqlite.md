
### Updating fields
UPDATE lock SET device_id='' WHERE id='';

### Delete a table
DROP TABLE device;"

### List tables
.tables

### See contents of a table
SELECT * FROM lock;

### Add records to table
INSERT INTO lock (room_id, device_id, api_key_env) VALUES ('537928-1', 'e90f7dd1-...', 'SEAM_KEY_1');

INSERT INTO lock (room_id, device_id, api_key_env) VALUES
  ('537928-1', 'device-uuid-here', 'SEAM_KEY_1'),
  ('537928-2', 'device-uuid-here', 'SEAM_KEY_1'),
  ('537928-3', 'device-uuid-here', 'SEAM_KEY_1');
