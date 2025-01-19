document.addEventListener("DOMContentLoaded", function() {
    const userId = sessionStorage.getItem('user_id');
    if (!userId) {
        alert("User ID is not set. Please log in again.");
        return;
    }

    fetch(`/api/user/${userId}`)
        .then(response => response.json())
        .then(data => {
            console.log("Fetched user data:", data); // Debugging information
            const bookedClassesContainer = document.getElementById('bookedClasses');
            bookedClassesContainer.innerHTML = '';

            data.children.forEach(child => {
                const childClasses = data.classes[child._id] || [];
                console.log(`Classes for ${child.first_name} ${child.last_name}:`, childClasses); // Debugging information
                const childSection = document.createElement('div');
                childSection.innerHTML = `
                    <h3>${child.first_name} ${child.last_name}</h3>
                    <ul>
                        ${childClasses.length > 0 ? childClasses.map(classInfo => `
                            <li>
                                ${classInfo.class_name} (${classInfo.class_date} ${classInfo.class_start_time} - ${classInfo.class_end_time})
                                <button onclick="removeBooking('${classInfo.booking_id}')">Remove</button>
                            </li>
                        `).join('') : '<li>No upcoming classes</li>'}
                    </ul>
                `;
                bookedClassesContainer.appendChild(childSection);
            });

            const userClasses = data.classes[userId] || [];
            console.log(`Classes for ${data.first_name} ${data.last_name}:`, userClasses); // Debugging information
            const userSection = document.createElement('div');
            userSection.innerHTML = `
                <h3>${data.first_name} ${data.last_name}</h3>
                <ul>
                    ${userClasses.length > 0 ? userClasses.map(classInfo => `
                        <li>
                            ${classInfo.class_name} (${classInfo.class_date} ${classInfo.class_start_time} - ${classInfo.class_end_time})
                            <button onclick="removeBooking('${classInfo.booking_id}')">Remove</button>
                        </li>
                    `).join('') : '<li>No upcoming classes</li>'}
                </ul>
            `;
            bookedClassesContainer.appendChild(userSection);
        })
        .catch(error => {
            console.error("Error fetching user data:", error); // Debugging information
        });
});

function removeBooking(bookingId) {
    if (confirm("Are you sure you want to remove this booking?")) {
        fetch(`/api/remove-booking/${bookingId}`, {
            method: 'POST'
        }).then(response => response.json())
          .then(result => {
              if (result.success) {
                  alert("Booking removed successfully!");
                  location.reload();
              } else {
                  alert(result.error);
              }
          })
          .catch(error => {
              console.error("Error removing booking:", error); // Debugging information
          });
    }
}
