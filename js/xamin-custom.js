/*
Template: Xamin -Data Science & Analytics HTML Template
Author: iqonicthemes.in
Version: 1.1
Design and Developed by: iqonicthemes.in
*/

/*----------------------------------------------
Index Of Script
------------------------------------------------
1. Back To Top
2. Wow Animation
3. Top menu sticky
4. Owl Carousel
5. Isotope
6. Accordion
7.Progress Bar
8. Page Loader
9.Magnific Popup
------------------------------------------------
Index Of Script
----------------------------------------------*/

(function (jQuery) {

	"use strict";

	function activaTab(pill) {
		jQuery(pill).addClass('active show');
	}

	jQuery(window).on('load', function (e) {
		jQuery('ul.page-numbers').addClass('justify-content-center');

		// Back To Top
		jQuery('#back-to-top').fadeOut();

		// Wow Animation
		var wow = new WOW({
			boxClass: 'wow',
			animateClass: 'animated',
			offset: 0,
			mobile: false,
			live: true
		});
		wow.init();

		jQuery('.sub-menu').css('display', 'none');
		jQuery('.sub-menu').prev().addClass('isubmenu');
		/*jQuery(".sub-menu").before('<i class="fa fa-angle-down toggledrop" aria-hidden="true"></i>');*/


		jQuery("#top-menu .menu-item .toggledrop").off("click");
		if (jQuery(window).width() < 992) {
			jQuery('#top-menu .menu-item .toggledrop').on('click', function (e) {
				e.preventDefault();
				jQuery(this).next('.children, .sub-menu').slideToggle();
			});
		}
	});

	jQuery(window).on('resize', function () {

		jQuery("#top-menu .menu-item .toggledrop").off("click");
		if (jQuery(window).width() < 992) {
			jQuery('#top-menu .menu-item .toggledrop').on('click', function (e) {
				e.preventDefault();
				jQuery(this).next('.children, .sub-menu').slideToggle();
			});
		}

		jQuery('.widget .fa.fa-angle-down, #main .fa.fa-angle-down').on('click', function () {
			jQuery(this).next('.children, .sub-menu').slideToggle();
		});

		jQuery("#top-menu .menu-item .toggledrop").off("click");
		if (jQuery(window).width() < 992) {
			jQuery('#top-menu .menu-item .toggledrop').on('click', function (e) {
				e.preventDefault();
				jQuery(this).next('.children, .sub-menu').slideToggle();
			});
		}
	});

	/*------------------------
	Tabs
	--------------------------*/
	jQuery(window).on('scroll', function (e) {
		//top menu sticky
		if (jQuery(this).scrollTop() > 10) {
			jQuery('header').addClass('menu-sticky');
		} else {
			jQuery('header').removeClass('menu-sticky');
		}

		// Pill Tab
		var nav = jQuery('#pills-tab');
		if (nav.length) {
			var contentNav = nav.offset().top - window.outerHeight;
			if (jQuery(window).scrollTop() >= (contentNav)) {
				e.preventDefault();
				jQuery('#pills-tab li a').removeClass('active');
				jQuery('#pills-tab li a[aria-selected=true]').addClass('active');
			}
		}

		// Feature Tab
		var nav1 = jQuery('#features');
		if (nav1.length) {
			var contentNav1 = nav1.offset().top - window.outerHeight;
			if (jQuery(window).scrollTop() >= (contentNav1)) {
				e.preventDefault();
				jQuery('#features .row li a').removeClass('active');
				jQuery('#features .row li a[aria-selected=true]').addClass('active');
			}
		}

		//Back To Top
		if (jQuery(this).scrollTop() > 250) {
			jQuery('#back-to-top').fadeIn(1400);
		} else {
			jQuery('#back-to-top').fadeOut(400);
		}
	});

	/*---------------------------
	Tabs
	---------------------------*/
	jQuery(document).ready(function () {

		// scroll body to 0px on click
		jQuery('#top').on('click', function () {
			jQuery('top').tooltip('hide');
			jQuery('body,html').animate({
				scrollTop: 0
			}, 800);
			return false;
		});

		// Owl Carousel
		jQuery('.owl-carousel').each(function () {
			var jQuerycarousel = jQuery(this);
			jQuerycarousel.owlCarousel({
				items: jQuerycarousel.data("items"),
				loop: jQuerycarousel.data("loop"),
				margin: jQuerycarousel.data("margin"),
				nav: jQuerycarousel.data("nav"),
				dots: jQuerycarousel.data("dots"),
				autoplay: jQuerycarousel.data("autoplay"),
				autoplayTimeout: jQuerycarousel.data("autoplay-timeout"),
				navText: ["<i class='fa fa-angle-left fa-2x'></i>", "<i class='fa fa-angle-right fa-2x'></i>"],
				responsiveClass: true,
				responsive: {
					// breakpoint from 0 up
					0: {
						items: jQuerycarousel.data("items-mobile-sm"),
						nav: false,
						dots: false
					},
					// breakpoint from 480 up
					480: {
						items: jQuerycarousel.data("items-mobile"),
						nav: false,
						dots: true,
						
					},
					// breakpoint from 786 up
					768: {
						items: jQuerycarousel.data("items-tab")
					},
					// breakpoint from 1023 up
					1023: {
						items: jQuerycarousel.data("items-laptop")
					},
					1199: {
						items: jQuerycarousel.data("items")
					}
				}
			});
		});

		  /*------------------------
        2 Isotope
        --------------------------*/
        if($(".isotope").length){
         $('.isotope').isotope({
            itemSelector: '.iq-grid-item',
        });

        // filter items on button click
        $('.isotope-filters').on('click', 'button', function() {
            var filterValue = $(this).attr('data-filter');
            $('.isotope').isotope({
                resizable: true,
                filter: filterValue
            });
            $('.isotope-filters button').removeClass('active');
            $(this).addClass('active');
        });
    }
        /*------------------------
        3 Masonry
        --------------------------*/
         if($(".iq-masonry-block").length){   
        var $msnry = $('.iq-masonry-block .iq-masonry');
        if ($msnry) {
            var $filter = $('.iq-masonry-block .isotope-filters');
            $msnry.isotope({
                percentPosition: true,
                resizable: true,
                itemSelector: '.iq-masonry-block .iq-masonry-item',
                masonry: {
                    gutterWidth: 0
                }
            });
            // bind filter button click
            $filter.on('click', 'button', function() {
                var filterValue = $(this).attr('data-filter');
                $msnry.isotope({
                    filter: filterValue
                });
            });

            $filter.each(function(i, buttonGroup) {
                var $buttonGroup = $(buttonGroup);
                $buttonGroup.on('click', 'button', function() {
                    $buttonGroup.find('.active').removeClass('active');
                    $(this).addClass('active');
                });
            });
        }
    }
		/*------------------------
		Accordion
		--------------------------*/
		jQuery('.iq-accordion .iq-accordion-block .accordion-details').hide();
		jQuery('.iq-accordion .iq-accordion-block:first').addClass('accordion-active').children().slideDown('slow');
		jQuery('.iq-accordion .iq-accordion-block').on("click", function () {
			if (jQuery(this).children('div.accordion-details ').is(':hidden')) {
				jQuery('.iq-accordion .iq-accordion-block').removeClass('accordion-active').children('div.accordion-details ').slideUp('slow');
				jQuery(this).toggleClass('accordion-active').children('div.accordion-details ').slideDown('slow');
			}
		});

		jQuery('.iq-faq .iq-block .iq-details').hide();
		jQuery('.iq-faq .iq-block:first').addClass('iq-active').children().slideDown('slow');
		jQuery('.iq-faq .iq-block').on("click", function() {
			if (jQuery(this).children('div').is(':hidden')) {
				jQuery('.iq-faq .iq-block').removeClass('iq-active').children('div').slideUp('slow');
				jQuery(this).toggleClass('iq-active').children('div').slideDown('slow');
			}
		});
		
		/*------------------------
		Progress Bar
		--------------------------*/
		jQuery('.iq-progress-bar > span').each(function () {
			var jQuerythis = jQuery(this);
			var width = jQuery(this).data('percent');
			jQuerythis.css({
				'transition': 'width 2s'
			});
			setTimeout(function () {
				jQuerythis.appear(function () {
					jQuerythis.css('width', width + '%');
				});
			}, 500);
		});

		jQuery('.nav.nav-pills').each(function () {
			var b = jQuery(this).find('a.active').attr('href');
			activaTab(b);
		});

		/*------------------------
		Page Loader
		--------------------------*/
		jQuery("#load").fadeOut();
		jQuery("#loading").delay(0).fadeOut("slow");

		// Video MagnificPopup
		jQuery('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
			disableOn: 700,
			type: 'iframe',
			mainClass: 'mfp-fade',
			removalDelay: 160,
			preloader: false,
			fixedContentPos: false
		});

		jQuery('.widget .fa.fa-angle-down, #main .fa.fa-angle-down').on('click', function () {
			jQuery(this).next('.children, .sub-menu').slideToggle();
		});

		jQuery('.timer').countTo();
	});
})(jQuery);

/*----------------------------------------------
Oxlon Shared Navigation
Single source of truth for header menu + footer quick links.
Edit NAV_ITEMS once to update all pages.
----------------------------------------------*/
(function () {
	"use strict";

	var NAV_ITEMS = [{
		label: "Home",
		href: "index.html"
	}, {
		label: "About Us",
		href: "about-us.html"
	}, {
		label: "Services",
		href: "services.html",
		children: [{
			label: "Data Analytics",
			href: "data-analytics.html"
		}, {
			label: "Managed Analytics",
			href: "managed-analytics.html"
		}, {
			label: "Big Data Services",
			href: "big-data-services.html"
		}, {
			label: "Data Science Consulting",
			href: "data-science-consulting.html"
		}, {
			label: "Business Intelligence",
			href: "business-intelligence.html"
		}, {
			label: "Data Visualization",
			href: "data-visualization-services.html"
		}, {
			label: "Data Management",
			href: "data-management.html"
		}, {
			label: "Artificial Intelligence",
			href: "artificial-intelligence.html"
		}]
	}, {
		label: "Contact",
		href: "contact-us.html"
	}];

	function toPagePath(url) {
		if (!url) {
			return "index.html";
		}

		var cleaned = url.split("#")[0].split("?")[0];
		var parts = cleaned.split("/");
		var leaf = parts[parts.length - 1];
		return leaf || "index.html";
	}

	function currentPagePath() {
		return toPagePath(window.location.pathname);
	}

	function isActive(item, page) {
		if (toPagePath(item.href) === page) {
			return true;
		}

		if (!item.children || !item.children.length) {
			return false;
		}

		for (var i = 0; i < item.children.length; i += 1) {
			if (toPagePath(item.children[i].href) === page) {
				return true;
			}
		}

		return false;
	}

	function buildHeaderItem(item, page) {
		var activeClass = isActive(item, page) ? " current-menu-item" : "";

		if (item.children && item.children.length) {
			var submenu = '<ul class="sub-menu">';
			for (var i = 0; i < item.children.length; i += 1) {
				var child = item.children[i];
				var childActive = toPagePath(child.href) === page ? " current-menu-item" : "";
				submenu += '<li class="menu-item' + childActive + '"><a href="' + child.href + '">' + child.label + "</a></li>";
			}
			submenu += "</ul>";

			return '<li class="menu-item' + activeClass + '"><a href="' + item.href + '" class="isubmenu">' + item.label + '</a> <i class="fa fa-angle-down toggledrop" aria-hidden="true"></i>' + submenu + "</li>";
		}

		return '<li class="menu-item' + activeClass + '"><a href="' + item.href + '">' + item.label + "</a></li>";
	}

	function renderHeaderMenus() {
		var page = currentPagePath();
		var menus = document.querySelectorAll("ul#top-menu");
		if (!menus.length) {
			return;
		}

		var html = "";
		for (var i = 0; i < NAV_ITEMS.length; i += 1) {
			html += buildHeaderItem(NAV_ITEMS[i], page);
		}

		for (var m = 0; m < menus.length; m += 1) {
			menus[m].innerHTML = html;
		}
	}

	function renderFooterQuickLinks() {
		var page = currentPagePath();
		var wrappers = document.querySelectorAll(".menu-footer-menu-container");
		if (!wrappers.length) {
			return;
		}

		var links = "";
		for (var i = 0; i < NAV_ITEMS.length; i += 1) {
			var item = NAV_ITEMS[i];
			var activeClass = toPagePath(item.href) === page ? " current-menu-item" : "";
			links += '<li class="menu-item' + activeClass + '"><a href="' + item.href + '">' + item.label + "</a></li>";
		}

		for (var w = 0; w < wrappers.length; w += 1) {
			var list = wrappers[w].querySelector("ul.menu");
			if (!list) {
				list = document.createElement("ul");
				list.className = "menu";
				wrappers[w].innerHTML = "";
				wrappers[w].appendChild(list);
			}
			list.innerHTML = links;
		}
	}

	function initSharedNavigation() {
		renderHeaderMenus();
		renderFooterQuickLinks();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", initSharedNavigation);
	} else {
		initSharedNavigation();
	}
})();
