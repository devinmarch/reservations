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
let availability = {}; // { roomTypeId: { available, rate } }
let addedRooms = [];    // [ { roomTypeId, guests } ]

// Helpers
function setButtonState(btn, disabled, text) {
    btn.disabled = disabled;
    if (text !== undefined) btn.textContent = text;
}

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

function getDates() {
    return {
        checkIn: document.getElementById('check-in').value,
        checkOut: document.getElementById('check-out').value
    };
}

function getFormValues() {
    return {
        checkIn: document.getElementById('check-in').value,
        checkOut: document.getElementById('check-out').value,
        firstName: document.getElementById('first-name').value,
        lastName: document.getElementById('last-name').value,
        otaRef: document.getElementById('ota-ref').value,
        notes: document.getElementById('notes').value
    };
}

// Modal open/close
createBtn.addEventListener('click', () => {
    modal.classList.add('active');
    resetForm();
});

closeBtn.addEventListener('click', () => modal.classList.remove('active'));
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
});

// Check availability
checkAvailabilityBtn.addEventListener('click', async () => {
    const { checkIn, checkOut } = getDates();

    if (!checkIn || !checkOut) {
        alert('Please select check-in and check-out dates');
        return;
    }

    if (checkOut <= checkIn) {
        alert('Check-out must be after check-in');
        return;
    }

    setButtonState(checkAvailabilityBtn, true, 'Checking...');

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
        setButtonState(checkAvailabilityBtn, false, 'Check Availability');
    }
});

function renderAvailability() {
    availabilityResults.style.display = 'block';

    const checkIn = document.getElementById('check-in').value;
    const checkOut = document.getElementById('check-out').value;
    const nights = Math.round((new Date(checkOut) - new Date(checkIn)) / 86400000);

    let html = '';
    let hasAvailability = false;

    for (const [roomTypeId, info] of Object.entries(availability)) {
        const roomType = ROOM_TYPES[roomTypeId];
        if (roomType && info.available > 0) {
            const rate = `$${Number(info.rate).toFixed(2)}`;
            html += `<tr><td>${roomType.name}</td><td>${info.available}</td><td>${rate}</td></tr>`;
            hasAvailability = true;
        }
    }

    if (!hasAvailability) {
        availabilityResults.innerHTML = '<strong>No rooms available for selected dates</strong>';
        addRoomBtn.disabled = true;
        return;
    }

    availabilityResults.innerHTML = `
        <strong>Availability for a ${nights} night stay:</strong>
        <table style="width:100%; margin-top:8px; border-collapse:collapse;">
            <tr style="text-align:left; border-bottom:1px solid #ccc;">
                <th>Room</th><th>Available</th><th>OTA Rate</th>
            </tr>
            ${html}
        </table>`;
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

    const roomTypeSelect = div.querySelector('.room-type-select');
    const guestSelect = div.querySelector('.guest-count-select');
    const removeBtn = div.querySelector('.remove-room-btn');

    // Event listeners
    roomTypeSelect.addEventListener('change', (e) => onRoomTypeChange(e, index));
    guestSelect.addEventListener('change', (e) => {
        addedRooms[index].guests = parseInt(e.target.value);
    });
    removeBtn.addEventListener('click', () => removeRoom(index));
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

    // Re-render other room dropdowns to update availability counts
    updateAllRoomDropdowns();
    updateConfirmButton();
}

function getRemainingAvailability(roomTypeId) {
    const total = (availability[roomTypeId] || {}).available || 0;
    const used = addedRooms.filter(r => r.roomTypeId === roomTypeId).length;
    return total - used;
}

function updateAllRoomDropdowns() {
    const selects = roomsContainer.querySelectorAll('.room-type-select');
    selects.forEach((select) => {
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

    const { checkIn, checkOut, firstName, lastName, otaRef, notes } = getFormValues();
    const rooms = addedRooms.filter(r => r.roomTypeId);

    if (rooms.length === 0) {
        alert('Please add at least one room');
        return;
    }

    setButtonState(confirmBtn, true, 'Creating...');

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
        setButtonState(confirmBtn, false, 'Confirm Reservation');
    }
});
