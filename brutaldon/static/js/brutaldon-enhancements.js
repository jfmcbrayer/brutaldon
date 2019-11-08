String.prototype.trunc = 
    function(n){
        return this.substr(0,n-1)+(this.length>n?'&hellip;':'');
    };

function setTitle(user, page)
{
    document.title = `Brutaldon (${user}) – ${page}`;
}

function afterPage(user, page)
{
    setTitle(user,page);
    var menu = document.querySelector('#navMenu');
    menu.classList.remove('is-active');
    var burger = document.querySelector('.navbar-burger');
    burger.classList.remove('is-active');
    $('#page-load-indicator').hide();
}

function menuPrepare() {
    // Remove is-active from navbar menu
    var menu = document.querySelector('#navMenu');
    menu.classList.remove('is-active');

    // Pin the navbar to the top
    document.querySelector('body').classList.toggle("has-navbar-fixed-top");
    document.querySelector('nav.navbar').classList.toggle("is-fixed-top");

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

function expandCWButtonPrepare()
{
    var theButton = document.querySelector('#expandCWs');
    if (!theButton) {
        theButton = document.createElement('button');
        theButton.id = "expandCWs";
        theButton.textContent = "Expand CWs";
        theButton.classList.toggle('button');
        var title = document.querySelector('#title');
        if (title)
        {
            title.insertAdjacentElement('afterend', theButton);
            var details = document.querySelectorAll('details');
            var openState = false;

            if (details != null) {
                theButton.addEventListener('click', function() {
                    openState = details.item(0).hasAttribute('open');
                    details.forEach(function ($el) {
                        if (openState)
                        {
                            $el.removeAttribute('open');
                        } else
                        {
                            $el.setAttribute('open', '');
                        }
                    });
                    openState = !openState;
                    if (openState) { theButton.textContent = 'Collapse CWs'; }
                    else { theButton.textContent = "Expand CWs"; };
                    theButton.classList.toggle('is-active');
                });
            }
        }
    }
}

function fileButtonUpdaters()
{
    var file1 = document.getElementById("id_media_file_1");
    file1.onchange = function(){
        if (file1.files.length > 0)
        {
            document.getElementById('media_filename_1').innerHTML =  file1.files[0].name.trunc(5);
        }
    };
    var file2 = document.getElementById("id_media_file_2");
    file2.onchange = function(){
        if (file2.files.length > 0)
        {
            document.getElementById('media_filename_2').innerHTML =  file2.files[0].name.trunc(5);
        }
    };
    var file3 = document.getElementById("id_media_file_3");
    file3.onchange = function(){
        if (file3.files.length > 0)
        {
            document.getElementById('media_filename_3').innerHTML =  file3.files[0].name.trunc(5);
        }
    };
    var file4 = document.getElementById("id_media_file_4");
    file4.onchange = function(){
        if (file4.files.length > 0)
        {
            document.getElementById('media_filename_4').innerHTML =  file4.files[0].name.trunc(5);
        }
    };

}

function characterCountSetup()
{
    if ($("#id_status").length) {
        $("#status_count").text(characterCount());
        $("#id_status").keyup(function(){
            $("#status_count").text(characterCount());
        });
        $("#id_spoiler_text").keyup(function(){
            $("#status_count").text(characterCount());
        });
    }
}

function characterCount()
{
    return $("#id_status").val().length + $("#id_spoiler_text").val().length;
}

