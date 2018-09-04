function scrollTop()
{
    window.scrollTo(0,0);
    return true;
}

function setTitle(user, page)
{
    document.title = `Brutaldon (${user}) – ${page}`;
}

function afterPage(user, page)
{
    scrollTop();
    setTitle(user,page);
    var menu = document.querySelector('#navMenu');
    menu.classList.remove('is-active');
    var burger = document.querySelector('.navbar-burger');
    burger.classList.remove('is-active');
}

function menuPrepare() {
    // Remove is-active from navbar menu
    var menu = document.querySelector('#navMenu');
    menu.classList.remove('is-active');

    // Add the burger
    var brand = document.querySelector('.navbar-brand');
    var burger = document.createElement('a');
    burger.classList.toggle('navbar-burger');
    burger.setAttribute("aria-label", "menu");
    burger.setAttribute("aria-expanded", "false");
    burger.setAttribute("data-target", "navMenu");
    for (var index = 0; index < 3; index++)
    {
        var span = document.createElement('span');
        span.setAttribute('aria-hidden', "true");
        burger.appendChild(span);
    }
    brand.appendChild(burger);



    // Get all "navbar-burger" elements
    var $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);

    // Check if there are any navbar burgers
    if ($navbarBurgers.length > 0) {

        // Add a click event on each of them
        $navbarBurgers.forEach(function ($el) {
            $el.addEventListener('click', function () {

                // Get the target from the "data-target" attribute
                var target = $el.dataset.target;
                var $target = document.getElementById(target);

                // Toggle the class on both the "navbar-burger" and the "navbar-menu"
                $el.classList.toggle('is-active');
                $target.classList.toggle('is-active');

            });
        });
    }

}
