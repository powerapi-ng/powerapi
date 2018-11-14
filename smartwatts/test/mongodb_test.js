// Javascript script for create test environment with MongoDB
// !! You don't have to run this script manually, it's done
// !! in "mongodb.sh" bash script

// Create "test_puller" database
conn = new Mongo();
db = conn.getDB("test_puller");

// Recreate empty collection "test_puller1" "test_puller2"
db.test_puller1.drop()
db.test_puller2.drop()
db.createCollection("test_puller1");
db.createCollection("test_puller2");

// Feed the collection "test_puller1"
// with HWPCReport
for (var i = 0 ; i < 10 ; i++)
{
 db.test_puller1.insert({
  timestamp: Date.now(),
  sensor: 'sensor_test',
  target: 'system',
  megagroup: {
   0 : {
    0 : {
     'event1': 100,
     'event2': 200
    }
   }
  }
 })
}
