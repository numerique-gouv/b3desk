<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">

    <meta charset="utf-8">


    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
      </div>




        </div>


          </div>
        </div>
          </div>
        </div>
</html>
