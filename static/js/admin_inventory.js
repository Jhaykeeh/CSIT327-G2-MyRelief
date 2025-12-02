function deleteFamily(userId) {
            if (confirm('Are you sure you want to delete this family?')) {
                window.location.href = `/admin/delete-family/${userId}/`;
            }
        }

function editFamily(userId, name, address) {
            // You can open a modal or redirect to edit page
            alert(`Edit functionality for ${name} - Coming soon!`);
        }

        // Auto-hide messages after 3 seconds
        setTimeout(() => {
            const messages = document.querySelectorAll('[style*="position: fixed"]');
            messages.forEach(msg => msg.style.display = 'none');
        }, 3000);