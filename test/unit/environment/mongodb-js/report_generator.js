// Javascript script for create test environment with MongoDB
// !! You don't have to run this script manually, it's done
// !! in "mongodb.sh" bash script

function generate_hwpc(id, sensor, target) {
 return {
  _id: id,
  timestamp: Date.now(),
  sensor: sensor,
  target: target,
  groups: {
   megagroup: {
    0 : {
     0 : {
      'event1': 100,
      'event2': 200
     }
    }
   }
  }
 };
}
