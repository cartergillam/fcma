const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const currentDate = new Date();
let currentWeekStart = new Date(currentDate.setDate(currentDate.getDate() - currentDate.getDay()));
const header = document.getElementById("currentWeek");
const daysContainer = document.querySelector(".days");
const sideMenu = document.getElementById("sideMenu");
const selectedDateElement = document.getElementById("selectedDate");
const classList = document.getElementById("classList");
let selectedDate = null;
let isMonthlyView = false;
const toggleViewBtn = document.getElementById("toggleViewBtn");
const isAdmin = document.body.classList.contains('admin');

toggleViewBtn.addEventListener("click", () => {
    isMonthlyView = !isMonthlyView;
    toggleViewBtn.textContent = isMonthlyView ? "Switch to Current Week" : "Switch to Monthly View";
    if (!isMonthlyView) {
        currentWeekStart = new Date(currentDate.setDate(currentDate.getDate() - currentDate.getDay()));
    }
    fetchClassesAndRender();
});

function renderCalendar(classes) {
    if (isMonthlyView) {
        renderMonthlyCalendar(classes);
    } else {
        renderWeeklyCalendar(classes);
    }
}

function formatTime(time) {
    const [hour, minute] = time.split(':');
    const hourInt = parseInt(hour);
    const period = hourInt >= 12 ? 'PM' : 'AM';
    const formattedHour = hourInt % 12 || 12;
    return `${formattedHour}:${minute} ${period}`;
}

function formatTime24(time) {
    const [timePart, period] = time.split(' ');
    let [hour, minute] = timePart.split(':');
    hour = parseInt(hour);
    if (period === 'PM' && hour !== 12) {
        hour += 12;
    } else if (period === 'AM' && hour === 12) {
        hour = 0;
    }
    return `${String(hour).padStart(2, '0')}:${minute}`;
}

function renderWeeklyCalendar(classes) {
    header.textContent = `${monthNames[currentWeekStart.getMonth()]} ${currentWeekStart.getDate()} - ${monthNames[new Date(currentWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000).getMonth()]} ${new Date(currentWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000).getDate()}`;
    daysContainer.innerHTML = "";

    for (let i = 0; i < 7; i++) {
        const date = new Date(currentWeekStart.getTime() + i * 24 * 60 * 60 * 1000);
        const dateString = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        const dateCell = document.createElement("div");
        dateCell.textContent = date.getDate();
        if (currentDate.toDateString() === date.toDateString()) {
            dateCell.classList.add("today");
        }
        if (classes[dateString]) {
            classes[dateString].forEach(classInfo => {
                const classDiv = document.createElement("div");
                classDiv.classList.add("class-item");
                classDiv.innerHTML = `
                    ${classInfo.class_name} (${formatTime(classInfo.class_start_time)} - ${formatTime(classInfo.class_end_time)})
                    <br>Students: ${classInfo.current_students}/${classInfo.max_students}
                `;
                dateCell.appendChild(classDiv);
            });
        }
        dateCell.addEventListener("click", () => {
            if (selectedDate === dateString) {
                selectedDate = null;
                closeSideMenu();
                document.querySelectorAll(".days div").forEach(cell => cell.classList.remove("selected"));
            } else {
                selectedDate = dateString;
                document.querySelectorAll(".days div").forEach(cell => cell.classList.remove("selected"));
                dateCell.classList.add("selected");
                showClassesForDate(dateString, classes[dateString] || []);
            }
        });
        daysContainer.appendChild(dateCell);
    }
}

function renderMonthlyCalendar(classes) {
    header.textContent = `${monthNames[currentWeekStart.getMonth()]} ${currentWeekStart.getFullYear()}`;
    daysContainer.innerHTML = "";

    const firstDayOfMonth = new Date(currentWeekStart.getFullYear(), currentWeekStart.getMonth(), 1);
    const lastDayOfMonth = new Date(currentWeekStart.getFullYear(), currentWeekStart.getMonth() + 1, 0);
    const startDate = new Date(firstDayOfMonth.setDate(firstDayOfMonth.getDate() - firstDayOfMonth.getDay()));
    const endDate = new Date(lastDayOfMonth.setDate(lastDayOfMonth.getDate() + (6 - lastDayOfMonth.getDay())));

    for (let date = startDate; date <= endDate; date.setDate(date.getDate() + 1)) {
        const dateString = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        const dateCell = document.createElement("div");
        dateCell.textContent = date.getDate();
        if (currentDate.toDateString() === date.toDateString()) {
            dateCell.classList.add("today");
        }
        if (classes[dateString]) {
            classes[dateString].forEach(classInfo => {
                const classDiv = document.createElement("div");
                classDiv.classList.add("class-item");
                classDiv.innerHTML = `
                    ${classInfo.class_name} (${formatTime(classInfo.class_start_time)} - ${formatTime(classInfo.class_end_time)})
                    <br>Students: ${classInfo.current_students}/${classInfo.max_students}
                `;
                dateCell.appendChild(classDiv);
            });
        }
        dateCell.addEventListener("click", () => {
            if (selectedDate === dateString) {
                selectedDate = null;
                closeSideMenu();
                document.querySelectorAll(".days div").forEach(cell => cell.classList.remove("selected"));
            } else {
                selectedDate = dateString;
                document.querySelectorAll(".days div").forEach(cell => cell.classList.remove("selected"));
                dateCell.classList.add("selected");
                showClassesForDate(dateString, classes[dateString] || []);
            }
        });
        daysContainer.appendChild(dateCell);
    }
}

function showClassesForDate(date, classes) {
    selectedDateElement.textContent = date;
    classList.innerHTML = "";
    if (classes.length === 0) {
        classList.textContent = "No classes on this day.";
    } else {
        classes.forEach(classInfo => {
            const classItem = document.createElement("div");
            classItem.classList.add("class-item");
            classItem.innerHTML = `
                <div>${classInfo.class_name} (${formatTime(classInfo.class_start_time)} - ${formatTime(classInfo.class_end_time)})</div>
                <div>Students: ${classInfo.current_students}/${classInfo.max_students}</div>
                ${isAdmin ? `
                    <button onclick="viewClassDetails('${classInfo._id}')">View</button>
                    <button onclick="editClass('${classInfo._id}')">Edit</button>
                    <button onclick="deleteClass('${classInfo._id}')">Delete</button>
                ` : `
                    <button onclick="bookClass('${classInfo._id}')">Book</button>
                `}
            `;
            classList.appendChild(classItem);
        });
    }
    openSideMenu();
}

function editClass(classId) {
    fetch(`/api/class/${classId}`)
        .then(response => response.json())
        .then(data => {
            editClassForm.style.display = "block";
            classList.innerHTML = "";
            editClassForm.classList.add("editing");
            editClassForm.dataset.classId = classId;
            document.getElementById("editClassName").value = data.class_name;
            document.getElementById("editClassDate").value = data.class_date;
            document.getElementById("editClassStartTime").value = formatTime(data.class_start_time);
            document.getElementById("editClassEndTime").value = formatTime(data.class_end_time);
            document.getElementById("editClassStartTime_24").value = data.class_start_time; // Set hidden input value
            document.getElementById("editClassEndTime_24").value = data.class_end_time; // Set hidden input value
            document.getElementById("editMaxStudents").value = data.max_students;
            sideMenu.style.display = "block"; // Ensure the side menu is visible
            daysContainer.classList.add("locked"); // Lock the days
        });
}

editClassForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const classId = editClassForm.dataset.classId;
    const formData = new FormData(editClassForm);
    const data = Object.fromEntries(formData);
    data.class_start_time = document.getElementById("editClassStartTime_24").value; // Use hidden input value
    data.class_end_time = document.getElementById("editClassEndTime_24").value; // Use hidden input value
    data.max_students = parseInt(data.max_students);  // Ensure max_students is an integer
    fetch(`/api/edit-class/${classId}`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(result => {
          if (result.success) {
              fetchClassesAndRender();
              editClassForm.style.display = "none";
              daysContainer.classList.remove("locked"); // Unlock the days
              selectedDate = null; // Unselect the day
              sideMenu.style.display = "none"; // Hide the side menu
              selectedDateElement.textContent = ""; // Clear the selected date text
              classList.innerHTML = ""; // Clear the class list
              document.querySelectorAll(".days div").forEach(cell => cell.classList.remove("selected"));
          } else {
              alert(result.error);
          }
      });
});

function viewClassDetails(classId) {
    fetch(`/api/class/${classId}`)
        .then(response => response.json())
        .then(data => {
            const classDetails = `
                <h3>${data.class_name} <span class="close-btn" onclick="closeClassDetails()">x</span></h3>
                <p>Date: ${data.class_date}</p>
                <p>Time: ${formatTime(data.class_start_time)} - ${formatTime(data.class_end_time)}</p>
                <p>Max Students: ${data.max_students}</p>
                <p>Current Students: ${data.current_students}</p>
                <h4>Students:</h4>
                <ul>
                    ${data.students.map(student => `<li>${student.first_name} ${student.last_name}</li>`).join('')}
                </ul>
            `;
            classList.innerHTML = classDetails;
            sideMenu.style.display = "block";
        });
}

function closeClassDetails() {
    if (selectedDate) {
        fetch(`/api/classes?year=${currentWeekStart.getFullYear()}&month=${currentWeekStart.getMonth() + 1}`)
            .then(response => response.json())
            .then(data => {
                showClassesForDate(selectedDate, data.classes[selectedDate] || []);
            });
    }
}

function openSideMenu() {
    document.getElementById("sideMenu").classList.add("open");
}

function closeSideMenu() {
    document.getElementById("sideMenu").classList.remove("open");
    selectedDate = null; // Reset selectedDate to allow reopening
}

document.getElementById("discardChangesBtn").addEventListener("click", () => {
    editClassForm.style.display = "none";
    daysContainer.classList.remove("locked"); // Unlock the days
    selectedDate = null; // Unselect the day
    sideMenu.style.display = "none"; // Hide the side menu
    selectedDateElement.textContent = ""; // Clear the selected date text
    classList.innerHTML = ""; // Clear the class list
    fetchClassesAndRender();
});

document.getElementById("prevWeekBtn").addEventListener("click", () => {
    if (isMonthlyView) {
        currentWeekStart.setMonth(currentWeekStart.getMonth() - 1);
    } else {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
    }
    fetchClassesAndRender();
});

document.getElementById("nextWeekBtn").addEventListener("click", () => {
    if (isMonthlyView) {
        currentWeekStart.setMonth(currentWeekStart.getMonth() + 1);
    } else {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
    }
    fetchClassesAndRender();
});

function fetchClassesAndRender() {
    fetch(`/api/classes?year=${currentWeekStart.getFullYear()}&month=${currentWeekStart.getMonth() + 1}`)
        .then(response => response.json())
        .then(data => {
            renderCalendar(data.classes);
        });
}

function deleteClass(classId) {
    if (confirm("Are you sure you want to delete this class?")) {
        fetch(`/remove-class/${classId}`, {
            method: 'POST'
        }).then(() => {
            fetchClassesAndRender();
            closeSideMenu(); // Ensure the side menu is closed
        });
    }
}

function bookClass(classId) {
    const userId = sessionStorage.getItem('user_id');
    if (!userId) {
        alert("User ID is not set. Please log in again.");
        return;
    }

    fetch(`/api/user/${userId}`)
        .then(response => response.json())
        .then(data => {
            const students = [{ _id: userId, first_name: data.first_name, last_name: data.last_name }, ...data.children];
            const studentSelection = students.map(student => `
                <div>
                    <input type="checkbox" id="${student._id}" name="students" value="${student._id}">
                    <label for="${student._id}">${student.first_name} ${student.last_name}</label>
                </div>
            `).join('');

            const studentSelectionPopup = `
                <div class="popup">
                    <h3>Select Students</h3>
                    <form id="studentSelectionForm">
                        ${studentSelection}
                        <button type="submit">Book</button>
                        <button type="button" onclick="closePopup()">Cancel</button>
                    </form>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', studentSelectionPopup);

            document.getElementById('studentSelectionForm').addEventListener('submit', function(event) {
                event.preventDefault();
                const selectedStudents = Array.from(document.querySelectorAll('input[name="students"]:checked')).map(checkbox => checkbox.value);
                if (selectedStudents.length === 0) {
                    alert("Please select at least one student.");
                    return;
                }

                fetch(`/api/book-class/${classId}`, {
                    method: 'POST',
                    body: JSON.stringify({ child_ids: selectedStudents }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }).then(response => response.json())
                  .then(result => {
                      if (result.success) {
                          alert("Class booked successfully!");
                          fetchClassesAndRender();
                          closePopup();
                      } else {
                          alert(result.error);
                      }
                  });
            });
        });
}

function closePopup() {
    const popup = document.querySelector('.popup');
    if (popup) {
        popup.remove();
    }
}

function viewChildDetails(childId) {
    fetch(`/api/child/${childId}`)
        .then(response => response.json())
        .then(data => {
            const childDetails = `
                <h3>${data.first_name} ${data.last_name}</h3>
                <p>Email: ${data.email}</p>
                <p>Phone: ${data.phone}</p>
            `;
            classList.innerHTML = childDetails;
            sideMenu.style.display = "block";
        });
}

// Automatically fetch and render classes when the page loads
document.addEventListener("DOMContentLoaded", function() {
    fetchClassesAndRender();
});