// DOM elements
const modal = document.getElementById('create-modal');
const createBtn = document.getElementById('create-btn');
const closeBtn = document.getElementById('modal-close');
const checkAvailabilityBtn = document.getElementById('check-availability-btn');
const addRoomBtn = document.getElementById('add-room-btn');
const confirmBtn = document.getElementById('confirm-btn');
const availabilityResults = document.getElementById('availability-results');
const roomsContainer = document.getElementById('rooms-container');
const form = document.getElementById('create-form');

// State
let availability = {}; // { roomTypeId: availableCount }
let addedRooms = [];    // [ { roomTypeId, guests } ]

// Modal open/close
createBtn.addEventListener('click', () => {
    modal.classList.add('active');
    resetForm();
});

closeBtn.addEventListener('click', () => modal.classList.remove('active'));
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
});

function resetForm() {
    form.reset();
    availability = {};
    addedRooms = [];
    availabilityResults.style.display = 'none';
    availabilityResults.innerHTML = '';
    roomsContainer.innerHTML = '';
    addRoomBtn.disabled = true;
    confirmBtn.disabled = true;
}

// Check availability
checkAvailabilityBtn.addEventListener('click', async () => {
    const checkIn = document.getElementById('check-in').value;
    const checkOut = document.getElementById('check-out').value;

    if (!checkIn || !checkOut) {
        alert('Please select check-in and check-out dates');
        return;
    }

    if (checkOut <= checkIn) {
        alert('Check-out must be after check-in');
        return;
    }

    checkAvailabilityBtn.disabled = true;
    checkAvailabilityBtn.textContent = 'Checking...';

    try {
        const resp = await fetch('/ota/availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ checkIn, checkOut })
        });
        const data = await resp.json();

        if (!resp.ok) {
            throw new Error(data.error || 'Failed to check availability');
        }

        availability = data.availability;
        renderAvailability();
        addRoomBtn.disabled = false;

        // Clear any previously added rooms since dates changed
        addedRooms = [];
        roomsContainer.innerHTML = '';
        updateConfirmButton();

    } catch (err) {
        alert(err.message);
    } finally {
        checkAvailabilityBtn.disabled = false;
        checkAvailabilityBtn.textContent = 'Check Availability';
    }
});

function renderAvailability() {
    availabilityResults.style.display = 'block';
    let html = '<strong>Available:</strong><br>';
    let hasAvailability = false;

    for (const [roomTypeId, count] of Object.entries(availability)) {
        const roomType = ROOM_TYPES[roomTypeId];
        if (roomType && count > 0) {
            html += `${roomType.name}: ${count} available<br>`;
            hasAvailability = true;
        }
    }

    if (!hasAvailability) {
        html = '<strong>No rooms available for selected dates</strong>';
        addRoomBtn.disabled = true;
    }

    availabilityResults.innerHTML = html;
}

// Add room
addRoomBtn.addEventListener('click', () => {
    const roomIndex = addedRooms.length;
    addedRooms.push({ roomTypeId: '', guests: 1 });
    renderRoomEntry(roomIndex);
    updateConfirmButton();
});

function renderRoomEntry(index) {
    const div = document.createElement('div');
    div.className = 'room-entry';
    div.dataset.index = index;

    const existingRoom = addedRooms[index];
    const selectedRoomTypeId = existingRoom.roomTypeId || '';

    // Room type dropdown - restore selection if exists
    let roomOptions = '<option value="">Select room...</option>';
    for (const [roomTypeId, info] of Object.entries(ROOM_TYPES)) {
        let available = getRemainingAvailability(roomTypeId);
        if (selectedRoomTypeId === roomTypeId) available += 1;
        if (available > 0) {
            const selected = selectedRoomTypeId === roomTypeId ? 'selected' : '';
            roomOptions += `<option value="${roomTypeId}" ${selected}>${info.name} (${available} left)</option>`;
        }
    }

    // Guest dropdown - restore if room type was selected
    let guestOptions = '<option value="1">1 guest</option>';
    let guestDisabled = 'disabled';
    if (selectedRoomTypeId) {
        const maxGuests = ROOM_TYPES[selectedRoomTypeId].maxGuests || 2;
        guestOptions = '';
        for (let i = 1; i <= maxGuests; i++) {
            const selected = existingRoom.guests === i ? 'selected' : '';
            guestOptions += `<option value="${i}" ${selected}>${i} guest${i > 1 ? 's' : ''}</option>`;
        }
        guestDisabled = '';
    }

    div.innerHTML = `
        <select class="room-type-select" data-index="${index}">${roomOptions}</select>
        <select class="guest-count-select" data-index="${index}" ${guestDisabled}>${guestOptions}</select>
        <button type="button" class="btn btn-danger remove-room-btn" data-index="${index}">Remove</button>
    `;

    roomsContainer.appendChild(div);

    // Event listeners
    div.querySelector('.room-type-select').addEventListener('change', (e) => onRoomTypeChange(e, index));
    div.querySelector('.guest-count-select').addEventListener('change', (e) => {
        addedRooms[index].guests = parseInt(e.target.value);
    });
    div.querySelector('.remove-room-btn').addEventListener('click', () => removeRoom(index));
}

function onRoomTypeChange(e, index) {
    const roomTypeId = e.target.value;
    addedRooms[index].roomTypeId = roomTypeId;

    const guestSelect = e.target.parentElement.querySelector('.guest-count-select');

    if (roomTypeId) {
        const maxGuests = ROOM_TYPES[roomTypeId].maxGuests || 2;
        let options = '';
        for (let i = 1; i <= maxGuests; i++) {
            options += `<option value="${i}">${i} guest${i > 1 ? 's' : ''}</option>`;
        }
        guestSelect.innerHTML = options;
        guestSelect.disabled = false;
        addedRooms[index].guests = 1;
    } else {
        guestSelect.innerHTML = '<option value="1">1 guest</option>';
        guestSelect.disabled = true;
    }

    guestSelect.addEventListener('change', (e) => {
        addedRooms[index].guests = parseInt(e.target.value);
    });

    // Re-render other room dropdowns to update availability counts
    updateAllRoomDropdowns();
    updateConfirmButton();
}

function getRemainingAvailability(roomTypeId) {
    const total = availability[roomTypeId] || 0;
    const used = addedRooms.filter(r => r.roomTypeId === roomTypeId).length;
    return total - used;
}

function updateAllRoomDropdowns() {
    const selects = roomsContainer.querySelectorAll('.room-type-select');
    selects.forEach((select, idx) => {
        const currentValue = select.value;
        let options = '<option value="">Select room...</option>';

        for (const [roomTypeId, info] of Object.entries(ROOM_TYPES)) {
            let available = getRemainingAvailability(roomTypeId);
            // Add back 1 if this dropdown currently has this room selected
            if (currentValue === roomTypeId) available += 1;

            if (available > 0) {
                const selected = currentValue === roomTypeId ? 'selected' : '';
                options += `<option value="${roomTypeId}" ${selected}>${info.name} (${available} left)</option>`;
            }
        }

        select.innerHTML = options;
    });
}

function removeRoom(index) {
    addedRooms.splice(index, 1);
    roomsContainer.innerHTML = '';
    addedRooms.forEach((_, i) => renderRoomEntry(i));
    updateConfirmButton();
}

function updateConfirmButton() {
    const hasRooms = addedRooms.some(r => r.roomTypeId);
    confirmBtn.disabled = !hasRooms;
}

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const checkIn = document.getElementById('check-in').value;
    const checkOut = document.getElementById('check-out').value;
    const firstName = document.getElementById('first-name').value;
    const lastName = document.getElementById('last-name').value;
    const otaRef = document.getElementById('ota-ref').value;
    const notes = document.getElementById('notes').value;

    const rooms = addedRooms.filter(r => r.roomTypeId);

    if (rooms.length === 0) {
        alert('Please add at least one room');
        return;
    }

    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Creating...';

    try {
        const resp = await fetch('/ota/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                checkIn,
                checkOut,
                firstName,
                lastName,
                otaRef,
                notes,
                rooms
            })
        });

        const data = await resp.json();

        if (!resp.ok) {
            throw new Error(data.error || 'Failed to create reservation');
        }

        alert('Reservation created successfully!');
        window.location.reload();

    } catch (err) {
        alert(err.message);
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Reservation';
    }
});
