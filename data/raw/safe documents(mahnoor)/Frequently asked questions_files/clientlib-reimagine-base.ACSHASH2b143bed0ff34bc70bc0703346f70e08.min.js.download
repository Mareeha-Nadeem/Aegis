// This function replaces popover data-island tags insertd in RTE via the popover plugin
(function () {
    if (!window || !window.ocrReimagine) {
        return;
    }

    window.ocrReimagine.PopoverRichTextPlugin = new class {
        popoverRichTextMountSelector = '.popover-rte-mount';
        popoverMountSelector = '[data-mount="popover"]';

        isPopoverComponentEnabled() {
            return !!(window.mwf?.Popover);
        }

        isIconComponentEnabled() {
            return !!(window.ocrReimagine?.Icon?.getInstances());
        }

        /**
         * Initialize popover elements with the class 'popover-rte-mount' by looking up inside the target element or entire document.
         */
        initializePopoverRichTextPlugin() {
            if (!this.isPopoverComponentEnabled()) {
                return;
            }

            // Get all popover rich text elements.
            const popoverRichTextElements = this.getPopoverRichTextElements();

            if (!popoverRichTextElements) {
                return;
            }

            // Create a custom template for each popover rich text element.
            this.createPopoverRichTextTemplate(popoverRichTextElements);

            // Initialize popovers for elements with the attribute 'data-mount="popover"'.
            this.initializePopoverComponent();

            // Remove popover instances that are no longer in the DOM.
            // this.cleanupInstances();
        }

        /**
         * Initialize popovers for elements with the attribute 'data-mount="popover"'.
         * For each matching element, create a new Popover instance and add it to the list of instances.
         */
        initializePopoverComponent() {
            // Get existing popover instances.
            const popoverInstances = window.mwf.Popover.getInstances() || [];
            // Get all popover mount elements.
            const popoverMounts = this.getPopoverMountElements();

            if (!popoverMounts) {
                return;
            }

            // For each popover mount element, create a new Popover instance and add it to the list of instances.
            popoverMounts.forEach((popoverMount) => {
                const popoverId = popoverMount.id;
                const popoverInstance = popoverInstances.find((instance) => instance.el.id === popoverId);

                if (!popoverInstance) {
                    new window.mwf.Popover({ el: popoverMount });
                }
            });
        }

        /**
         * Removes popover instances that are no longer in the DOM.
         */
        cleanupInstances() {
            // Get existing popover instances.
            const popoverInstances = window.mwf.Popover.getInstances() || [];

            let instanceCount = popoverInstances.length;
            while (instanceCount--) {
                try {
                    const instance = popoverInstances[instanceCount];
                    const popoverId = instance?.el?.id;

                    // Skip if popover ID is not available.
                    if (!popoverId) {
                        continue;
                    }

                    const popoverMountedElement = document.getElementById(popoverId);

                    // Remove the instance if the popover mount element is no longer in the DOM.
                    if (!popoverMountedElement) {
                        instance.remove();
                    }

                    // Find duplicate instances within the list of instances.
                    const duplicateInstances = popoverInstances.filter((item) => item.el.id === popoverId);

                    // Remove the duplicate instances.
                    if (duplicateInstances.length > 1) {
                        duplicateInstances.forEach((item, index) => {
                            if (index > 0) {
                                item.remove();
                            }
                        });
                    }
                }
                catch (e) {
                }
            }
        }

        /**
         * Gets all popover rich text elements.
         * 
         * @returns {NodeListOf<Element>} List of all popover rich text elements.
         */
        getPopoverRichTextElements() {
            return document.querySelectorAll(this.popoverRichTextMountSelector);
        }

        /**
         * Gets all popover mount elements.
         * 
         * @returns {NodeListOf<Element>} List of all popover mount elements.
         */
        getPopoverMountElements() {
            return document.querySelectorAll(this.popoverMountSelector);
        }

        /**
         * For each element, replaces it with a custom template and initialize an Icon object if enabled.
         * 
         * @param {NodeListOf<Element>} popoverRichTextElements 
         */
        createPopoverRichTextTemplate(popoverRichTextElements) {
            popoverRichTextElements.forEach((element) => {
                const id = this.getUniqueId();
                const text = element.getAttribute('data-text');
                const description = element.getAttribute('data-description');
                const screenReaderText = element.getAttribute('data-screenReaderText');
                const template = document.createRange().createContextualFragment(this.getPopoverTemplate(text, description, screenReaderText, id));

                // Replace the current popover element with the custom template.
                element.replaceWith(template);

                // Check if Icon is enabled and if there are Icon instances available.
                if (this.isIconComponentEnabled()) {
                    this.initializeIconObjects(id);
                }
            });
        }

        /**
         * Initializes an Icon object for a specified HTML element with the given ID and adds it to the list of instances.
         * @param {string} id - The ID of the HTML element to which the Icon object will be attached.
         * @returns {void}
         */
        initializeIconObjects(id) {
            const element = document.getElementById(id);

            if (!element) {
                return;
            }

            // Create a new Icon instance.
            new window.ocrReimagine.Icon({ el: element });
        }

        /**
         * Generates a version 4 UUID (Universally Unique Identifier).
         * @returns {string} A randomly generated version 4 UUID.
         */
        getUniqueId() {
            return crypto.randomUUID() ||
                ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
                    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
                );
        }

        /**
         * Generates HTML for a popover element with optional text, description, and screen reader text.
         * 
         * @param {string | null} text - The text content to display within the popover.
         * @param {string | null} description - The description of the popover.
         * @param {string | null} screenReaderText - The screen reader text for accessibility (optional).
         * @param {string} id - A unique identifier for the popover element.
         * @returns {string} The HTML markup for the popover element.
         */
        getPopoverTemplate(text, description, screenReaderText, id) {
            let textElement = '';

            if (text) {
                textElement = `<span class="popover__label">${text}</span>`
            }

            return `
            <span class="popover__content">
                ${textElement}
    
                <button class="popover__info" id="${id}" aria-controls="popover-window-${id}" data-mount="popover" data-placement="right" aria-expanded="false" aria-haspopup="dialog" aria-label="${screenReaderText ?? ''}">
                    <div class="ocr-icon ocr-icon--size-xs ocr-icon-svg--info-filled" aria-hidden="true" role="presentation">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" alt="">
                            <title class="sr-only">${screenReaderText ?? ''}</title>
                            <path></path>
                            <path></path>
                        </svg>
                    </div>
                </button>
            
                <div class="popover fade popover__card" id="popover-window-${id}" role="dialog" aria-labelledby="${id}">
                    <div>
                        <p class="popover__card-body m-0 x-small">${description ?? ''}</p>
                    </div>
                </div>
            </span>
    
            <style>
                .ocr-icon > svg > path {
                    d: path(var(--icon-svg-path));
                }
                /* this is specific to comment-note svg and the only instance of using 2 paths */
                .ocr-icon-svg--comment-note svg > path:nth-child(2) {
                    d: path(var(--icon-svg-path-2));
                }
            </style>
            `;
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        try {
            window.ocrReimagine.PopoverRichTextPlugin.initializePopoverRichTextPlugin();
        } catch (e) {
        }
    });
}());