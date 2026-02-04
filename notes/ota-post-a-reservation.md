# Create Reservation Feature for OTA

I'd like to start working on the next feature for the OTA service. The next feature is more or less the core and we built something similar in the past. I just have a better understanding now.

We need to allow the user to create a reservation which essentially makes a POST request to CloudBeds.

Here is how I see this working.

- We add a ‘Create Reservation’ button to the top right of the reservations table
- On click, a pop-up reveals an input form (unless you suggest a simpler UX)

## Form Structure
- Check-in and Check-out date fields
- ‘Check Availability’ button (makes getRatePlans call to CloudBeds with the date range and rateIDs. We will make a dictionary of rateIDs to use for this call.) The 'Check Availability button should be protected until the call has completed.

[Space for availability to populate]

- Under the availability section will be a greyed out ‘Add room’ button until the getRatePlans call returns available inventory for the date range. Rooms get added as objects, the add room UI helps us build a valid call.

Sample structure for rooms array

{
  "propertyID": "your_property_id",
  // ... other reservation details ...
  "rooms": {
    "0": "room_type_id_for_room_1", 
    "1": "room_type_id_for_room_2" 
  },
  "adults": {
    "0": "num_adults_for_room_1", 
    "1": "num_adults_for_room_2"
  },
  "children": {
    "0": "num_children_for_room_1", 
    "1": "num_children_for_room_2"
  }
}

- A line will populate with 2 drop downs Room Name from getRatePlans call, number of guests (we'll pre-determine the max number of guests in the dictionary). As lines are added you shouldn’t be able to add anymore of each type than was returned in the getRatePlans call.

- Primary Guest First Name and Last Name fields, OTA Ref. (thirdPartyIdentifier), 
	- We will fill in other required fields from the ota config file: Phone, Email, Country code, sourceID from dictionary (appended with: -1 at the end)

- A notes text field for the OTA to leave additional notes regarding the booking (during the postReservation process we will also post this note to the reservation)

- Lastly, a confirm reservation button. This should also be protected until the process runs and completes.

## Additional items to consider

- In order to avoid a double-booking, since CloudBeds doesn't error if you try to post too many rooms, on click of Confirm Reservation, I'd like to call getRatePlans again to confirm that the rooms we are posting are in fact still available.

- After the post has been made and before the process is complete we need to:
    1. Do a postAdjustment to the folio to adjust the rate. Initially I just want to calculate the adjustment by a specific percentage of the balance before taxes. Keeping in mind that in the futur I will want the ability to supply a dictionary of base rates per room type and the adjustment would be made as a reconciliation of the CloudBeds balance and what we determine the total to be based on our OTA config.
    2. Post the note to the reservation.
    3. Flash the reservation has been confirmed and redirect to the main OTA page which will reload with the new reservation fromt he workflow we already built.