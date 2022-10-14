local function ensureHtmlDeps()
  quarto.doc.addHtmlDependency({
    name = 'elevatorjs',
    version = '1.0.0',
    scripts = {"elevator.min.js"}
  })
end

local function isEmpty(s)
  return s == '' or s == nil
end

return {
  ["elevator"] = function(args, kwargs)
    if quarto.doc.isFormat("html:js") then
      ensureHtmlDeps()

      local textButton = 'Return to the top!'
      local targetAnchor = ''
      if #args > 0 then
        textButton = pandoc.utils.stringify(args[1])
        if #args > 1 then
          targetAnchor = 'targetElement: document.querySelector("#' .. pandoc.utils.stringify(args[2]) .. '"), '
        end
      end

      mainAudio = pandoc.utils.stringify(kwargs["audio"])
      if isEmpty(mainAudio) then
        mainAudio = ''
      end

      endAudio = pandoc.utils.stringify(kwargs["end"])
      if isEmpty(endAudio) then
        endAudio = "ding.mp3"
        quarto.doc.addFormatResource(endAudio)
      end

      return pandoc.RawInline(
        'html',
        '<script>' ..
          'window.onload = function() { ' ..
            'var elevator = new Elevator({ ' ..
              'element: document.querySelector(".elevator-button")' ..
              ', ' .. 
              targetAnchor ..
              ' mainAudio: "' .. mainAudio .. '",' ..
              ' endAudio: "' .. endAudio .. '"' ..
            ' });' ..
          ' }' ..
        '</script>' ..
        '<button class="btn btn-outline-primary elevator-button" type="submit">' .. textButton .. '</button>'
      )
    else
      return pandoc.Null()
    end
  end
}
