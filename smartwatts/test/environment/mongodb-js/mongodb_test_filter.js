// Javascript script for create test environment with MongoDB
// !! You don't have to run this script manually, it's done
// !! in "mongodb.sh" bash script

load('./mongodb-js/report_generator.js');

// Create "test_filter" database
conn = new Mongo();
db = conn.getDB("test_filter");

// Recreate empty collection "test_filter1"
db.test_filter1.drop()
db.createCollection("test_filter1");

// Feed the collection "test_filter1"
// with HWPCReport
sensors_name = ["sensor_test1", "sensor_test2", "sensor_test3"]
for (var n = 0 ; n < sensors_name.length ; n++)
{
 for (var i = 0 ; i < 2 ; i++)
 {
  db.test_filter1.insert(generate_hwpc(n*2+i, sensors_name[n], 'system'));
 }
}
