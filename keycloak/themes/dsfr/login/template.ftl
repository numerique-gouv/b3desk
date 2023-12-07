<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false displayWide=false showAnotherWayIfPresent=true>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">

    <#if properties.meta?has_content>
        <#list properties.meta?split(' ') as meta>
            <meta name="${meta?split('==')[0]}" content="${meta?split('==')[1]}"/>
        </#list>
    </#if>
    <title>${msg("loginTitle",(realm.displayName!''))}</title>
    <link rel="icon" href="${url.resourcesPath}/img/favicon.ico" />
    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${url.resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.scripts?has_content>
        <#list properties.scripts?split(' ') as script>
            <script src="${url.resourcesPath}/${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
        </#list>
    </#if>
</head>

<body>
<header class="rf-header">
  <div class="rf-container">
    <div class="rf-header__body">
      <div class="rf-header__brand">
  <a href="${properties.kcServiceTitle!}" style="box-shadow: none;"><span class="rf-logo rf-logo__title">
    République
    <br>française
  </span></a>
</div>
<div class="rf-header__navbar">
  <div class="rf-service">
    <!-- Webinaire de l'État -->
    <a class="rf-service__title" href="${properties.kcServiceTitle!}">Webinaire de l'État</a>
    <!-- Le service de réunions en ligne pour les agents de l'État -->
    <p class="rf-service__tagline">${properties.kcServiceTagline!}</p>
  </div>
</div>
      <div class="rf-header__tools">

<div class="rf-shortcuts">
    <ul class="rf-shortcuts__list">
		  <li class="rf-shortcuts__item">
        <a href="${properties.kcExternalFooterLinksBaseUrl!}/faq" target="_blank" class="rf-link rf-fi-information-line rf-link--icon-left" target="_self">Modalités d'accès</a>
      </li>
      <li class="rf-shortcuts__item">
        <a href="${properties.kcExternalFooterLinksBaseUrl!}/documentation" target="_blank" class="rf-link rf-fi-add-circle-line rf-link--icon-left">Lien vers la documentation</a>
      </li>
    </ul>
  </div></div>
    </div>
    <nav class="rf-nav" role="navigation" aria-label="Menu principal">
      <ul class="rf-nav__list">
         <li class="rf-nav__item">
         </li>
      </ul>
   </nav>
  </div>
</header>
<main role="main" id="main" class="rf-container" >
  <div class="rf-container  rf-mt-4w rf-mb-4w">
    <div class="rf-grid-row rf-grid-row--center">
      <div class="rf-col-xs-12 rf-col-sm-8 rf-col-md-6 rf-col-lg-8">

          <!--p>Domaine ${kcSanitize(msg("loginTitleHtml",(realm.displayNameHtml!'')))?no_esc}</p-->

              <#if realm.internationalizationEnabled  && locale.supported?size gt 1>
                  <div id="kc-locale">
                      <div id="kc-locale-wrapper" class="${properties.kcLocaleWrapperClass!}">
                          <div class="kc-dropdown" id="kc-locale-dropdown">
                              <a href="#" id="kc-current-locale-link">${locale.current}</a>
                              <ul>
                                  <#list locale.supported as l>
                                      <li class="kc-dropdown-item"><a href="${l.url}">${l.label}</a></li>
                                  </#list>
                              </ul>
                          </div>
                      </div>
                  </div>
              </#if>
              <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
                  <#if displayRequiredFields>
                      <div class="${properties.kcContentWrapperClass!}">
                          <div class="${properties.kcLabelWrapperClass!} subtitle">
                              <span class="subtitle"><span class="required">*</span> ${msg("requiredFields")}</span>
                          </div>
                          <div class="col-md-10">
                              <h1 id="kc-page-title"><#nested "header"></h1>
                          </div>
                      </div>
                  <#else>
                      <h1 id="kc-page-title"><#nested "header"></h1>
                  </#if>
              <#else>
                  <#if displayRequiredFields>
                      <div class="${properties.kcContentWrapperClass!}">
                          <div class="${properties.kcLabelWrapperClass!} subtitle">
                              <span class="subtitle"><span class="required">*</span> ${msg("requiredFields")}</span>
                          </div>
                          <div class="col-md-10">
                              <#nested "show-username">
                              <div class="${properties.kcFormGroupClass!}">
                                  <div id="kc-username">
                                      <label id="kc-attempted-username">${auth.attemptedUsername}</label>
                                      <a id="reset-login" href="${url.loginRestartFlowUrl}">
                                          <div class="kc-login-tooltip">
                                              <i class="${properties.kcResetFlowIcon!}"></i>
                                              <span class="kc-tooltip-text">${msg("restartLoginTooltip")}</span>
                                          </div>
                                      </a>
                                  </div>
                              </div>
                          </div>
                      </div>
                  <#else>
                      <#nested "show-username">
                      <div class="${properties.kcFormGroupClass!}">
                          <div id="kc-username">
                              <label id="kc-attempted-username">${auth.attemptedUsername}</label>
                              <a id="reset-login" href="${url.loginRestartFlowUrl}">
                                  <div class="kc-login-tooltip">
                                      <i class="${properties.kcResetFlowIcon!}"></i>
                                      <span class="kc-tooltip-text">${msg("restartLoginTooltip")}</span>
                                  </div>
                              </a>
                          </div>
                      </div>
                  </#if>
              </#if>

            <div id="kc-content">
            <div id="kc-content-wrapper">
              <#-- App-initiated actions should not see warning messages about the need to complete the action -->
              <#-- during login.                                                                               -->
              <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                  <div class="alert alert-${message.type}">
                      <#if message.type = 'success'><span class="${properties.kcFeedbackSuccessIcon!}"></span></#if>
                      <#if message.type = 'warning'><span class="${properties.kcFeedbackWarningIcon!}"></span></#if>
                      <#if message.type = 'error'><span class="${properties.kcFeedbackErrorIcon!}"></span></#if>
                      <#if message.type = 'info'><span class="${properties.kcFeedbackInfoIcon!}"></span></#if>
                      <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                  </div>
              </#if>

              <#nested "form">

              <#if auth?has_content && auth.showTryAnotherWayLink() && showAnotherWayIfPresent>
              <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post" <#if displayWide>class="${properties.kcContentWrapperClass!}"</#if>>
                  <div class="${properties.kcFormGroupClass!}">
                    <input type="hidden" name="tryAnotherWay" value="on" />
                    <a href="#" id="try-another-way" class="rf-link" onclick="document.forms['kc-select-try-another-way-form'].submit();return false;">${msg("doTryAnotherWay")}</a>
                  </div>
              </form>
              </#if>

              <#if displayInfo>
                  <div id="kc-info">
                      <div id="kc-info-wrapper">
                          <#nested "info">
                      </div>
                  </div>
              </#if>
            </div>
          </div>
          </div>

      </div>
    </div>
  </div>
</main>
<footer class="rf-footer" role="contentinfo">
    <div class="rf-container">
        <div class="rf-footer__body">
            <div class="rf-footer__brand">
                <span class="rf-logo rf-logo__title">république<br>française</span>
            </div>
            <div class="rf-footer__content">
                <p class="rf-footer__content-desc">
                    Service proposé par la Direction interministérielle du numérique et la Direction du numérique pour l'éducation
                </p>
                <p class="rf-footer__content-desc">
                    Le code source est ouvert et les contributions sont bienvenues.
                    <a title="Voir le code source - nouvelle fenêtre" href="https://github.com/numerique-gouv/b3desk/" target="_blank" rel="noopener">Voir le code source</a>
                </p>

                <ul class="rf-footer__content-links">
                    <li>
                        <a href="https://legifrance.gouv.fr">legifrance.gouv.fr</a>
                    </li>
                    <li>
                        <a href="https://gouvernement.fr">gouvernement.fr</a>
                    </li>
                    <li>
                        <a href="https://service-public.fr">service-public.fr</a>
                    </li>
                    <li>
                        <a href="https://data.gouv.fr">data.gouv.fr</a>
                    </li>
                </ul>
            </div>
        </div>
        <div class="rf-footer__bottom">
            <ul class="rf-footer__bottom-list">
                <li>
                    <a href="${properties.kcExternalFooterLinksBaseUrl!}/accessibilite">Accessibilité : non conforme</a>                </li>
                <li>
                    <a href="${properties.kcExternalFooterLinksBaseUrl!}/mentions_legales">Mentions légales</a>
                </li>
                <li>
                    <a href="${properties.kcExternalFooterLinksBaseUrl!}/donnees_personnelles">Données personnelles et cookies</a>
                </li>
                <li>
                    <a href="${properties.kcExternalFooterLinksBaseUrl!}/cgu">Conditions générales d’utilisation</a>
                </li>
            </ul>
        </div>
    </div>
</footer>
</body>
</html>
</#macro>
