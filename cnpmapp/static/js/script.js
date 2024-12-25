document.addEventListener("DOMContentLoaded", () => {
    const currentPage = document.body.dataset.page;
    if (typeof currentPage !== "undefined") {
        switch (currentPage) {
            case "index": {
                dateInput();
                break;
            }
            case "reservation": {
                document.getElementById('num_people').value = 1;

                dateInput();
                updateReservationForm();
                break;
            }
            default:
                break;
        }
    }
});

window.onload = () => {
    const currentPage = document.body.dataset.page;
    if (typeof currentPage !== "undefined") {
        switch (currentPage) {
            case "index":
                break;
            case "reservation": {
                updateReservationDays();
                break;
            }
            default:
                break;
        }
    }
};

function dateInput() {
    const today = new Date();
    const formattedDate = today.toISOString().split("T")[0];
    const checkin = document.getElementById("checkin");
    const checkout = document.getElementById("checkout");

    let checkin_max = new Date();
    checkin_max.setDate(checkin_max.getDate() + 28);

    checkin.min = formattedDate;
    checkin.max = checkin_max.toISOString().split("T")[0];
    checkin.value = document.getElementById('checkin').value;

    let checkout_max = new Date();
    checkout_max.setDate(checkout_max.getDate() + 28);

    checkout.min = formattedDate;
    checkout.max = checkout_max.toISOString().split("T")[0];
    checkout.value = document.getElementById('checkout').value;

    checkin.addEventListener("change", () => {
        const checkinDate = checkin.value;
        if (checkinDate) {
            checkout.min = checkinDate;
            if (checkout.value < checkinDate) {
                checkout.value = "";
            }
        }
        updateReservationDays();
    });

    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener("keydown", (event) => {
            event.preventDefault();
        });
        input.addEventListener("mousedown", (event) => {
            event.preventDefault();
        });
    });

    document.getElementById('checkin').addEventListener('change', updateCheckoutDate);
    document.getElementById('checkout').addEventListener('change', updateReservationDays);

    function updateCheckoutDate() {
        let checkinDate = document.getElementById('checkin').value;
        let checkoutDate = document.getElementById('checkout').value;
        if (checkinDate && !checkoutDate) {
            let checkout = new Date(checkinDate);
            document.getElementById('checkout').value = checkout.toISOString().split('T')[0];
        }
        updateReservationDays();
    }
}

function updateReservationForm() {
    const numPeople = document.getElementById('num_people').value;
    const formContainer = document.getElementById('formContainer');
    formContainer.innerHTML = '';

    for (let i = 1; i <= numPeople; i++) {
        const formGroup = document.createElement('div');
        formGroup.className = 'reservation-form-group';
        formGroup.style.padding = '15px';
        formGroup.innerHTML = `
            <label for="person_${i}">Khách hàng ${i}: </label>
            <input type="text" name="person_${i}" id="person_${i}" class="form-control" placeholder="Tên khách hàng" required>
            <select id="country_${i}" name="country_${i}" class="form-select" aria-label="Loại khách" onchange="updateReservationPricing()">
                <option value="${0}">Ngoại quốc</option>
                <option value="${1}">Nội quốc</option>
            </select>
            <input type="tel" name="uid_${i}" id="uid_${i}" class="form-control" pattern="[0-9]*" placeholder="ID code (CMMD, CCCD)" required>
            <input type="tel" id="phone_${i}" name="phone_${i}" class="form-control" pattern="[0-9]{10-12}" minlength="10" maxlength="12" placeholder="số điện thoại" required>
            <input type="text" name="address_${i}" id="address_${i}" class="form-control" placeholder="Địa chỉ" required>
        `;
        formContainer.appendChild(formGroup);
    }
    updateReservationPricing();
}

function updateReservationDays() {
    const reservation_date_offer = document.getElementById('reservation-date_offer');
    if (reservation_date_offer !== null) {
        const checkinDate = new Date(document.getElementById('checkin').value);
        const checkoutDate = new Date(document.getElementById('checkout').value);
        if (checkoutDate >= checkinDate) {
            const timeDifference = checkoutDate - checkinDate;
            const daysDifference = 1 + timeDifference / (1000 * 60 * 60 * 24);
            reservation_date_offer.textContent = `Thời hạn: ${daysDifference} ngày`;
            updateReservationPricing();
        }
    }
}

function updateReservationPricing() {
    const roomId = document.getElementById('roomId').getAttribute('data-room-id');
    const numPeople = document.getElementById('num_people').value;
    const checkinDate = document.getElementById('checkin').value;
    const checkoutDate = document.getElementById('checkout').value;

    let domestic_count = 0;
    for (let i = 1; i <= numPeople; i++) {
        domestic_count += parseInt(document.getElementById(`country_${i}`).value);
    }
    let is_domestic = domestic_count >= numPeople ? 1 : 0;

    fetch(`/reservation/pricing`, {
        method: "post",
        body: JSON.stringify({
            "room_id": roomId,
            "num_people": numPeople,
            "is_domestic": is_domestic,
            "start_date": checkinDate,
            "end_date": checkoutDate,
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(response => response.json()).then(data => {
        const pricing = data.total_price;
        const pricingDisplay = document.getElementById('pricing');
        pricingDisplay.value = pricing;

        const totalPriceDisplay = document.getElementById('totalPrice');
        totalPriceDisplay.setAttribute('data-room-id', `${pricing}`);
        totalPriceDisplay.textContent = `Tổng số tiền: ${pricing.toLocaleString('vn-VN')} VNĐ`;
    });
}

function nextToReservation(room_id) {
    const checkin = document.getElementById('checkin').value;
    const checkout = document.getElementById('checkout').value;

    window.location.href = `/reservation/${room_id}&${checkin}&${checkout}`;
}

function booking_confirm(ticket_id, room_name){
    const checkin = document.getElementById('checkin').value;
    const checkout = document.getElementById('checkout').value;
    if (confirm(`Xác nhận lập phiếu thuê phòng ${room_name}, thời gian: từ ${checkin} đến ${checkout}`)) {
        fetch('/booking', {
            method:'post',
            body:JSON.stringify({
                'ticket_id' : ticket_id
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then(data=>{
            Swal.fire({
                icon: data.status,
                title: 'Lập phiếu thuê phòng',
                text: data.message,
                confirmButtonText: 'OK'
            }).then((result) => {
                if (result.isConfirmed) {
                    location.reload();
                }
            });
        })
    }
}

function payment_confirm(ticket_id, room_name) {
    const checkin = document.getElementById('checkin').value;
    const checkout = document.getElementById('checkout').value;
    if (confirm(`Xác nhận khách hàng đã thanh toán phòng ${room_name}, thời gian: từ ${checkin} đến ${checkout}`)) {
        fetch('/payment', {
            method:'post',
            body:JSON.stringify({
                'ticket_id' : ticket_id
            }),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => res.json()).then(data=>{
            Swal.fire({
                icon: data.status,
                title: 'Xác nhận thanh toán',
                text: data.message,
                confirmButtonText: 'OK'
            }).then((result) => {
                if (result.isConfirmed) {
                    location.reload();
                }
            });
        })
    }
}