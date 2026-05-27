/**
 * ============================================
 * MAIN.JS — Развивайся
 * Образовательная платформа по электробезопасности
 * ============================================
 * 
 * Содержит:
 * - Mobile Navigation (Burger Menu)
 * - Radio Button Selection
 * - Timer functionality
 * - Form handling utilities
 * - Backend integration helpers
 */

(function() {
    'use strict';

    // ===== DOM ELEMENTS =====
    const burgerMenu = document.getElementById('burgerMenu');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // ===== MOBILE NAVIGATION =====
    
    /**
     * Toggle mobile sidebar menu
     */
    function toggleMobileMenu() {
        if (burgerMenu && sidebar && sidebarOverlay) {
            burgerMenu.classList.toggle('active');
            sidebar.classList.toggle('active');
            sidebarOverlay.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
        }
    }

    /**
     * Close mobile menu
     */
    function closeMobileMenu() {
        if (burgerMenu && sidebar && sidebarOverlay) {
            burgerMenu.classList.remove('active');
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Event Listeners for mobile menu
    if (burgerMenu) {
        burgerMenu.addEventListener('click', toggleMobileMenu);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeMobileMenu);
    }

    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });

    // Close menu on window resize (if desktop width)
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMobileMenu();
        }
    });


    // ===== RADIO BUTTON SELECTION =====
    
    /**
     * Initialize radio button selection UI
     */
    function initRadioSelection() {
        const radioOptions = document.querySelectorAll('.radio-option');
        
        radioOptions.forEach(function(option) {
            option.addEventListener('click', function() {
                // Remove selected class from all options in the same group
                const form = this.closest('form') || this.closest('.radio-group');
                if (form) {
                    form.querySelectorAll('.radio-option').forEach(function(opt) {
                        opt.classList.remove('selected');
                    });
                }
                
                // Add selected class to clicked option
                this.classList.add('selected');
                
                // Check the radio input
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                }
            });
        });
    }

    initRadioSelection();


    // ===== TIMER FUNCTIONALITY =====
    
    /**
     * Timer class for training and exam
     */
    class Timer {
        constructor(displayElement, options = {}) {
            this.displayElement = displayElement;
            this.seconds = options.startSeconds || 0;
            this.countDown = options.countDown || false;
            this.maxSeconds = options.maxSeconds || null;
            this.onComplete = options.onComplete || null;
            this.onTick = options.onTick || null;
            this.interval = null;
        }

        /**
         * Format seconds to HH:MM:SS
         */
        formatTime(totalSeconds) {
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            
            return [hours, minutes, seconds]
                .map(function(val) {
                    return val.toString().padStart(2, '0');
                })
                .join(':');
        }

        /**
         * Update display
         */
        updateDisplay() {
            if (this.displayElement) {
                this.displayElement.textContent = this.formatTime(this.seconds);
            }
        }

        /**
         * Start timer
         */
        start() {
            if (this.interval) return;
            
            this.updateDisplay();
            
            this.interval = setInterval(() => {
                if (this.countDown) {
                    this.seconds--;
                    
                    if (this.seconds <= 0) {
                        this.seconds = 0;
                        this.stop();
                        if (this.onComplete) {
                            this.onComplete();
                        }
                    }
                } else {
                    this.seconds++;
                    
                    if (this.maxSeconds && this.seconds >= this.maxSeconds) {
                        this.stop();
                        if (this.onComplete) {
                            this.onComplete();
                        }
                    }
                }
                
                this.updateDisplay();
                
                if (this.onTick) {
                    this.onTick(this.seconds);
                }
            }, 1000);
        }

        /**
         * Stop timer
         */
        stop() {
            if (this.interval) {
                clearInterval(this.interval);
                this.interval = null;
            }
        }

        /**
         * Reset timer
         */
        reset(seconds = 0) {
            this.stop();
            this.seconds = seconds;
            this.updateDisplay();
        }

        /**
         * Get current seconds
         */
        getSeconds() {
            return this.seconds;
        }
    }

    // Initialize Training Timer (count up)
    const trainingTimerElement = document.getElementById('trainingTimer');
    if (trainingTimerElement) {
        const trainingTimer = new Timer(trainingTimerElement, {
            startSeconds: 0,
            countDown: false
        });
        
        trainingTimer.start();
        
        // Store timer reference for later use
        window.trainingTimer = trainingTimer;
    }

    // Initialize Exam Timer (countdown from 10 minutes)
    const examTimerElement = document.getElementById('examTimer');
    if (examTimerElement) {
        const examTimer = new Timer(examTimerElement, {
            startSeconds: 10 * 60, // 10 minutes
            countDown: true,
            onComplete: function() {
                // Backend: Auto-submit exam when time runs out
                alert('Время экзамена истекло! Экзамен будет автоматически завершен.');
                // window.location.href = 'exam-result-fail.html';
                console.log('Exam time expired. Implement auto-submit to backend.');
            },
            onTick: function(seconds) {
                // Warning when 1 minute left
                if (seconds === 60) {
                    examTimerElement.style.color = 'var(--color-error)';
                }
            }
        });
        
        examTimer.start();
        
        // Store timer reference for later use
        window.examTimer = examTimer;
    }


    // ===== FORM HANDLING =====
    
    /**
     * Get selected answer from form
     */
    function getSelectedAnswer(formId) {
        const form = document.getElementById(formId);
        if (!form) return null;
        
        const selected = form.querySelector('input[type="radio"]:checked');
        return selected ? selected.value : null;
    }

    /**
     * Validate that an answer is selected
     */
    function validateAnswerSelected(formId) {
        const answer = getSelectedAnswer(formId);
        if (!answer) {
            alert('Пожалуйста, выберите ответ');
            return false;
        }
        return true;
    }


    // ===== BUTTON HANDLERS =====
    
    // Previous Question Button (Training)
    const prevQuestionBtn = document.getElementById('prevQuestion');
    if (prevQuestionBtn) {
        prevQuestionBtn.addEventListener('click', function() {
            // Backend: Navigate to previous question
            console.log('Navigate to previous question');
            // Implement API call or state management
        });
    }

    // Check Answer Button (Training)
    const checkAnswerBtn = document.getElementById('checkAnswer');
    if (checkAnswerBtn) {
        checkAnswerBtn.addEventListener('click', function() {
            if (!validateAnswerSelected('answersForm')) return;
            
            const answer = getSelectedAnswer('answersForm');
            // Backend: Verify answer and show result
            console.log('Check answer:', answer);
            // Implement API call to verify answer
        });
    }

    // Next Question Button (Training)
    const nextQuestionBtn = document.getElementById('nextQuestion');
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', function() {
            if (!validateAnswerSelected('answersForm')) return;
            
            const answer = getSelectedAnswer('answersForm');
            // Backend: Save answer and navigate to next question
            console.log('Save answer and go to next:', answer);
            // Implement API call or state management
        });
    }

    // Next Question Button (Exam)
    const nextExamQuestionBtn = document.getElementById('nextExamQuestion');
    if (nextExamQuestionBtn) {
        nextExamQuestionBtn.addEventListener('click', function() {
            if (!validateAnswerSelected('examAnswersForm')) return;
            
            const answer = getSelectedAnswer('examAnswersForm');
            // Backend: Save answer and navigate to next question
            console.log('Save exam answer and go to next:', answer);
            // Implement API call - answers should be saved automatically
        });
    }

    // Finish Exam Button
    const finishExamBtn = document.getElementById('finishExam');
    if (finishExamBtn) {
        finishExamBtn.addEventListener('click', function() {
            const confirmed = confirm('Вы уверены, что хотите завершить экзамен? Это действие нельзя отменить.');
            
            if (confirmed) {
                // Stop timer
                if (window.examTimer) {
                    window.examTimer.stop();
                }
                
                // Backend: Submit exam and get results
                console.log('Finish exam - submit to backend');
                // Implement API call to submit exam
                // Redirect based on result:
                // window.location.href = 'exam-result-success.html';
                // or
                // window.location.href = 'exam-result-fail.html';
            }
        });
    }


    // ===== FILTER HANDLING (Training page) =====
    
    const resetFiltersBtn = document.getElementById('resetFilters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            const groupFilter = document.getElementById('groupFilter');
            const voltageFilter = document.getElementById('voltageFilter');
            
            if (groupFilter) groupFilter.selectedIndex = 0;
            if (voltageFilter) voltageFilter.selectedIndex = 0;
            
            // Backend: Reload tickets with no filters
            console.log('Filters reset');
            // Implement API call to reload tickets
        });
    }

    // Filter change handlers
    const groupFilter = document.getElementById('groupFilter');
    const voltageFilter = document.getElementById('voltageFilter');

    if (groupFilter) {
        groupFilter.addEventListener('change', function() {
            // Backend: Filter tickets by group
            console.log('Filter by group:', this.value);
            // Implement API call to filter tickets
        });
    }

    if (voltageFilter) {
        voltageFilter.addEventListener('change', function() {
            // Backend: Filter tickets by voltage
            console.log('Filter by voltage:', this.value);
            // Implement API call to filter tickets
        });
    }


    // ===== DOWNLOAD HANDLERS =====
    
    const downloadProtocolBtn = document.getElementById('downloadProtocol');
    if (downloadProtocolBtn) {
        downloadProtocolBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Backend: Generate and download protocol PDF
            console.log('Download protocol PDF');
            // Implement API call to generate/download PDF
        });
    }

    const downloadProtocolSuccessBtn = document.getElementById('downloadProtocolSuccess');
    if (downloadProtocolSuccessBtn) {
        downloadProtocolSuccessBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Backend: Download success protocol PDF
            console.log('Download success protocol PDF');
            // Implement API call
        });
    }

    const downloadProtocolFailBtn = document.getElementById('downloadProtocolFail');
    if (downloadProtocolFailBtn) {
        downloadProtocolFailBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Backend: Download fail protocol PDF
            console.log('Download fail protocol PDF');
            // Implement API call
        });
    }


    // ===== UTILITY FUNCTIONS FOR BACKEND INTEGRATION =====
    
    /**
     * API Helper for making requests
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise}
     */
    window.apiRequest = async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                // Backend: Add authorization header
                // 'Authorization': 'Bearer ' + getToken()
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    };

    /**
     * Load user data from API
     * Backend: Replace with actual API endpoint
     */
    window.loadUserData = async function() {
        try {
            // const userData = await apiRequest('/api/user');
            // Update UI with user data
            console.log('Load user data from API');
        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    };

    /**
     * Load tickets from API
     * Backend: Replace with actual API endpoint
     */
    window.loadTickets = async function(filters = {}) {
        try {
            // const tickets = await apiRequest('/api/tickets', {
            //     method: 'POST',
            //     body: JSON.stringify(filters)
            // });
            // Render tickets to grid
            console.log('Load tickets from API with filters:', filters);
        } catch (error) {
            console.error('Failed to load tickets:', error);
        }
    };

    /**
     * Load question from API
     * Backend: Replace with actual API endpoint
     */
    window.loadQuestion = async function(ticketId, questionIndex) {
        try {
            // const question = await apiRequest(`/api/tickets/${ticketId}/questions/${questionIndex}`);
            // Render question to UI
            console.log('Load question:', ticketId, questionIndex);
        } catch (error) {
            console.error('Failed to load question:', error);
        }
    };

    /**
     * Submit answer to API
     * Backend: Replace with actual API endpoint
     */
    window.submitAnswer = async function(ticketId, questionId, answerId) {
        try {
            // const result = await apiRequest('/api/answers', {
            //     method: 'POST',
            //     body: JSON.stringify({ ticketId, questionId, answerId })
            // });
            console.log('Submit answer:', ticketId, questionId, answerId);
        } catch (error) {
            console.error('Failed to submit answer:', error);
        }
    };

    /**
     * Submit exam to API
     * Backend: Replace with actual API endpoint
     */
    window.submitExam = async function(examId) {
        try {
            // const result = await apiRequest(`/api/exams/${examId}/submit`, {
            //     method: 'POST'
            // });
            // Redirect based on result
            console.log('Submit exam:', examId);
        } catch (error) {
            console.error('Failed to submit exam:', error);
        }
    };


    // ===== PROGRESS BAR UPDATE =====
    
    /**
     * Update progress bar
     * @param {number} current - Current question number
     * @param {number} total - Total questions
     */
    window.updateProgress = function(current, total) {
        const percentage = Math.round((current / total) * 100);
        
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.querySelector('.test-progress-text');
        const progressPercent = document.querySelector('.test-progress-percent');
        
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        
        if (progressText) {
            progressText.textContent = `Вопрос ${current} из ${total}`;
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${percentage}% выполнено`;
        }
    };


    // ===== INITIALIZATION =====
    
    console.log('Развивайся — Platform initialized');
    console.log('Backend integration points marked with "Backend:" comments');

})();
