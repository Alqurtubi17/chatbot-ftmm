class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.messages = [];
        this.lastVisitorMessageId = null;  // Keep track of the last visitor message ID
    }

    display() {
        const { openButton, chatBox, sendButton } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox);
            }
        });
    }

    toggleState(chatbox) {
        this.state = !this.state;
        if (this.state) {
            chatbox.classList.add('chatbox--active');
        } else {
            chatbox.classList.remove('chatbox--active');
        }
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value;
        if (text1 === "") {
            return;
        }
    
        // Periksa jika form feedback ada dan belum di-submit, tampilkan sweet alert
        if (this.lastVisitorMessageId && document.querySelector('.feedback-form')) {
            // Tampilkan sweet alert yang mengingatkan untuk mengisi feedback terlebih dahulu
            Swal.fire({
                title: 'Harap berikan feedback!',
                text: 'Tolong berikan feedback untuk pesan sebelumnya sebelum mengirim pesan lain agar FTMMQA dapat berkembang',
                icon: 'warning',
                confirmButtonText: 'Ok'
            });
            return;
        }
    
        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);
        
        fetch($SCRIPT_ROOT + '/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(r => r.json())
        .then(r => {
            let msg2 = { name: "FTMMQA", message: r.answer, id: r.message_id };
            this.messages.push(msg2);
            this.lastVisitorMessageId = r.message_id;  // Update last visitor message ID
            this.updateChatText(chatbox);
            textField.value = '';
        }).catch((error) => {
            console.error('Error:', error);
            textField.value = '';
        });
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach((item) => {
            if (item.name === "FTMMQA") {
                html += '<div class="messages__item messages__item--visitor" style="margin-bottom:30px">' + item.message + '</div>';
            } else {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>';
            }
        });
        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
        // If the last message was from the visitor and we haven't added feedback yet, add it
        if (this.lastVisitorMessageId && !document.querySelector('.feedback-form')) {
            chatmessage.innerHTML += `
                <div class="feedback-form" style="position: absolute; bottom: 80px; width: 80%;">
                    Apakah jawaban ini membantu? <br>
                    <label><input type="radio" name="feedback" value="Membantu"> Ya</label>
                    <label><input type="radio" name="feedback" value="Tidak"> Tidak</label>
                    <button onclick="chatbox.sendFeedback(${this.lastVisitorMessageId}, document.querySelector('input[name=feedback]:checked').value)">Kirim</button>
                </div>
            `;
        }

        // chatmessage.scrollTop = chatmessage.scrollHeight; // Auto-scroll to the last message
    }

    sendFeedback(messageId, value) {
        if (!value) {
            console.error('Feedback is not selected.');
            return;
        }
        fetch($SCRIPT_ROOT + '/feedback', {
            method: 'POST',
            body: JSON.stringify({ index: messageId, feedback: value }),
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback received:', data);
            // Remove the feedback form to prevent multiple submissions
            const feedbackForm = document.querySelector('.feedback-form');
            if (feedbackForm) {
                feedbackForm.remove();
            }
            // Reset the last visitor message ID
            this.lastVisitorMessageId = null;
            // Optionally, show a notification to the user that feedback was sent
        })
        .catch(error => console.error('Error sending feedback:', error));
    }
}

const chatbox = new Chatbox();
chatbox.display();

