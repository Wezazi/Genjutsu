from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.goto("https://instagram.com", wait_until="networkidle") #replace url with target website of choice
    
    
    client = page.context.new_cdp_session(page)

    #required to use certain methods:
    client.send("DOM.enable")
    client.send("Accessibility.enable")
    client.send("DOM.getDocument", {"depth": -1})
    client.send("CSS.enable")
    client.send("DOMSnapshot.enable")

    styleFilter = [
                #experiment with these

                "color", "background-color", "background-clip", "letter-spacing", "font-size", "font-weight", "font-family", "font-style", "line-height", "text-align",

                "border-bottom-left-radius", "border-bottom-color", "border-bottom-right-radius", "border-left-color", "border-right-color", "border-top-color", "border-top-left-radius", "border-top-right-radius", 
                "outline-color", "outline-width",  "outline-style", "box-shadow", "cursor",
                "border-top-width", "border-right-width", "border-left-width", "border-bottom-width", "border-bottom-style", "border-right-style", "border-top-style", "border-left-style",
                "border-end-end-radius", "border-end-start-radius", "border-inline-end-color", "border-inline-end-style", "border-inline-end-width", "border-inline-start-color", "border-inline-start-style", "border-inline-start-width", "border-start-end-radius", "border-start-start-radius",
                "opacity", "fill",

                #for img
                "border-image-slice", "border-image-width", "border-image-outset", "border-image-repeat", "object-fit", "min-width", "min-height",
                "background-image",

    ]

    shot = client.send("DOMSnapshot.captureSnapshot", {"computedStyles": styleFilter, "includePaintOrder": True, "includeDOMRects": True, "includeBlendedBackgroundColors": True, "includeTextColorOpacities": True})
    strings = shot["strings"]
    documents = shot["documents"]


    
    customDoc = []

    document = documents[0]

    
    documentUrl = document["documentURL"]
    title = document["title"]
    baseUrl = document["baseURL"]
    frameId = document["frameId"]
    scrollOffsetX = document["scrollOffsetX"]
    scrollOffsetY = document["scrollOffsetY"]
    contentWidth = document["contentWidth"]
    contentHeight = document["contentHeight"]

    nodes = document["nodes"]
    parentIndex = nodes["parentIndex"]
    nodeType = nodes["nodeType"]
    nodeName = nodes["nodeName"]
    nodeValue = nodes["nodeValue"]
    backendNodeId = nodes["backendNodeId"]
    attributes = nodes["attributes"] 
    inputValue = nodes["inputValue"]

    
    layout = document["layout"]
    nodeIndex = layout["nodeIndex"]
    styles = layout["styles"]
    layoutBounds = layout["bounds"]
    text = layout["text"]
    stackingContexts = layout["stackingContexts"] 
    paintOrders = layout["paintOrders"] 
    offsetRects = layout["offsetRects"]
    scrollRects = layout["scrollRects"]
    clientRects = layout["clientRects"]
    
    textBoxes = document["textBoxes"] 
    layoutIndex = textBoxes["layoutIndex"]
    textBoxesBounds = textBoxes["bounds"] 
    start = textBoxes["start"]
    length = textBoxes["length"]
    
    
    def stringVert(indexes):
         
        if isinstance(indexes, list):
            stringList = []
            for index in indexes:
                stringList.append(strings[index])
            return stringList
        else:
            return strings[indexes]
        
    title = stringVert(title)
    
              
         
    textBoxesInfo = {}

    textBoxesAmount = len(layoutIndex)
    for i in range(textBoxesAmount):
        
        lI = layoutIndex[i]

        textBoxesInfo[lI] = {
            "textBoxesBounds" : textBoxesBounds[i],
            "start" : start[i],
            "length" : length[i]
        }


    layoutInfo = {}

    layoutAmount = len(nodeIndex)
    for i in range(layoutAmount):
         
        nI = nodeIndex[i]
        cssValues = stringVert(styles[i])
        merge = {}
        for propName, propValue in zip(styleFilter, cssValues):
            merge[propName] = propValue
              

        layoutInfo[nI] = {
              
            "styles" : merge,
            "layoutBounds" : layoutBounds[i],
            "text" : stringVert(text[i]),
            #"stackingContexts" : stackingContexts,
            "paintOrders" : paintOrders[i],
            "offsetRects" : offsetRects[i],
            "scrollRects" : scrollRects[i],
            "clientRects" : clientRects[i],
            #"blendedBackgroundColors" : blendedBackgroundColors[i]
        }
        if i in textBoxesInfo:
            layoutInfo[nI].update(textBoxesInfo[i])

    
    nodeAmount = len(nodeValue)
    for i in range(nodeAmount):
        iV = ""
        for vI, vV in zip(inputValue["index"], inputValue["value"]):
            if vI == i:
                iV = stringVert(vV)
                break
            
        nodeInfo = {
            "index" : i,
            "parentIndex" : parentIndex[i],
            "nodeType" : nodeType[i],
            "nodeName" : stringVert(nodeName[i]).lower(),
            "nodeValue" : stringVert(nodeValue[i]),
            "backendNodeId" : backendNodeId[i],
            "attributes" : stringVert(attributes[i]),
            "inputValue": iV
            
        }
        if i in layoutInfo:
            nodeInfo.update(layoutInfo[i])

        customDoc.append(nodeInfo)

    #layoutbounds for textnodes with inline are not accurate so i use the quad method, this method will add some extra space between elements though, real nesting is always better
    for node in customDoc:
        req = [node["backendNodeId"]]
        frontId = client.send("DOM.pushNodesByBackendIdsToFrontend", {"backendNodeIds": req})
        nodeId = frontId["nodeIds"][0]
        node["nodeId"] = nodeId
        
        try:
            box = client.send("DOM.getContentQuads", {"nodeId": nodeId})
            quads = box.get("quads")

            quadList = []

            if quads:
                for quad in quads:
                    xs = quad[0::2]
                    ys = quad[1::2]

                    x = min(xs)
                    y = min(ys)
                    width = max(xs) - x
                    height = max(ys) - y

                    quadList.append({
                        "top": f"{y}px",
                        "left": f"{x}px",
                        "width": f"{width}px",
                        "height": f"{height}px"
                    })
            else:
                quadList.append({
                        "top": "0px",
                        "left": "0px",
                        "width": "0px",
                        "height": "0px"
                    })
            
        except Exception:
            quadList.append({
                        "top": "0px",
                        "left": "0px",
                        "width": "0px",
                        "height": "0px"
                    })
            
        node["quadList"] = quadList

    #set css properties here if you want to apply for all elements (excluding inline textnodes)
    for node in customDoc:
        if "layoutBounds" in node:
            node["layoutBounds"] = { #no need to check if layoutBounds are empty, if they exist then they will have values regardless if the node is an element or textnode.
                "position" : "absolute",
                "white-space": "nowrap",
                "box-sizing" : "border-box",
                "left" : f"{node["layoutBounds"][0]}px",
                "top" : f"{node["layoutBounds"][1]}px",
                "width" : f"{node["layoutBounds"][2]}px",
                "height" : f"{node["layoutBounds"][3]}px"
            }
        else:
            pass
        
        if "offsetRects" in node:
            if node["offsetRects"]: #check if offsetRects are empty or not, they will exist but be empty on textnodes
                node["offsetRects"] = {
                    "left" : f"{node["offsetRects"][0]}px",
                    "top" : f"{node["offsetRects"][1]}px",
                    "width" : f"{node["offsetRects"][2]}px",
                    "height" : f"{node["offsetRects"][3]}px"
                }
            else:
                pass
        else:
            pass
        
        if "scrollRects" in node:
            if node["scrollRects"]: #check if scrollRects are empty or not, they will exist but be empty on textnodes
                node["scrollRects"] = {
                    "left" : f"{node["scrollRects"][0]}px",
                    "top" : f"{node["scrollRects"][1]}px",
                    "width" : f"{node["scrollRects"][2]}px",
                    "height" : f"{node["scrollRects"][3]}px"
                }
            else:
                pass
        else:
            pass
        
        if "clientRects" in node:
            if node["clientRects"]: #check if clientRects are empty or not, they will exist but be empty on textnodes
                node["clientRects"] = {
                    "left" : f"{node["clientRects"][0]}px",
                    "top" : f"{node["clientRects"][1]}px",
                    "width" : f"{node["clientRects"][2]}px",
                    "height" : f"{node["clientRects"][3]}px"
                }
            else:
                pass
        else:
            pass
        #set css for inline textnodes
        if "textBoxesBounds" in node:
            node["textBoxesBounds"] = { #elements won't have textBoxesBounds so i don't need to check if empty, if a node has textBoxesBounds, then it has values
                "position" : "absolute",
                #"white-space": "nowrap",
                "box-sizing" : "border-box",
                "left" : f"{node["textBoxesBounds"][0]}px",
                "top" : f"{node["textBoxesBounds"][1]}px",
                "width" : f"{node["textBoxesBounds"][2]}px",
                "height" : f"{node["textBoxesBounds"][3]}px"
            }
        else:
            pass
    
    #splitting the inline part from the rest of the textnode
    for node in customDoc:
        if node["nodeType"] == 3:
            nV = node["nodeValue"]

            stringLength = len(nV)
            if "textBoxesBounds" in node:
                start = node["start"]
                length = node["length"]
                end = start + length
                magicNumber = end - start
                if magicNumber != stringLength:
                    node["inlineText"] = nV[start:end]
                    before = nV[:start]
                    node["realText"] = before
                    node["inlineStyles"] = {}
                    node["inlineStyles"].update(node["textBoxesBounds"])
                else:
                    node["realText"] = node["nodeValue"]
            else:
                node["realText"] = node["nodeValue"]

            node["nodeType"] = 1
            node["nodeName"] = "span"

    
    

    for node in customDoc:
        if "inlineStyles" in node:
            node["inlineStyles"].update(node["styles"])

        if "layoutBounds" in node:
            node["styles"].update(node["layoutBounds"])
        else:
            pass
    
    for node in customDoc:
        if node["nodeName"] == "i":
            node["output"] = []
            unlist = []
            node["styles"]["height"] = node["clientRects"]["height"]
            node["styles"]["width"] = node["clientRects"]["width"]


            if "styles" in node:
                for cssProperty, cssValue in node["styles"].items():
                    unlist.append(f"{cssProperty}: {cssValue}; ")
                joined = "".join(unlist)
                node["output"].append(f"#i{node['index']} {{{joined}}}")

                node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}'></{node['nodeName']}>")
            else:
                continue

        elif node["nodeName"] == "img":
            node["output"] = []
            unlist = []
            if "styles" in node:
                for cssProperty, cssValue in node["styles"].items():
                    unlist.append(f"{cssProperty}: {cssValue}; ")
                joined = "".join(unlist)
                node["output"].append(f"#i{node['index']} {{{joined}}}")

            unlist = []
            attr = node["attributes"]
            attrKeys = attr[0::2]
            attrValues = attr[1::2]

            for attrKey, attrValue in zip(attrKeys, attrValues):
                if attrKey == "src":
                    unlist.append(f"{attrKey}='{attrValue}' ")
                else:
                    continue
            joined = "".join(unlist)
            node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}' {joined}></{node['nodeName']}>")


        elif node["nodeName"] == "svg" or node["nodeName"] == "path":
            if "styles" in node:
                node["output"] = []
                unlist = []
                for cssProperty, cssValue in node["styles"].items():
                    unlist.append(f"{cssProperty}: {cssValue}; ")
                joined = "".join(unlist)
                node["output"].append(f"#i{node['index']} {{{joined}}}")

                
                unlist = []
                attr = node["attributes"]
                attrKeys = attr[0::2]
                attrValues = attr[1::2]


                for attrKey, attrValue in zip(attrKeys, attrValues):
                    unlist.append(f"{attrKey}='{attrValue}' ")
                joined = "".join(unlist)
                if node["nodeName"] == "svg":
                    node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}' {joined}>\n    place\n</{node['nodeName']}>")
                else:
                    node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}' {joined}></{node['nodeName']}>")
            else:
                continue

        elif "inlineStyles" in node:
            node["output"] = []
            unlist = []
            firstQuad = node["quadList"][0]
            node["styles"]["top"] = firstQuad["top"]
            node["styles"]["left"] = firstQuad["left"]
            node["styles"]["height"] = firstQuad["height"]
            node["styles"]["width"] = firstQuad["width"]

            for cssProperty, cssValue in node["inlineStyles"].items():
                unlist.append(f"{cssProperty}: {cssValue}; ")
            joined = "".join(unlist)
            node["output"].append(f"#inline-i{node['index']} {{{joined}}}")

            unlist = []
            for cssProperty, cssValue in node["styles"].items():
                unlist.append(f"{cssProperty}: {cssValue}; ")
            joined = "".join(unlist)
            node["output"].append(f"#i{node['index']} {{{joined}}}")

            rT = node["realText"]

            node["output"].insert(0, f"<{node['nodeName']} id='inline-i{node['index']}'>{node['inlineText']}</{node['nodeName']}>")
            node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}'>{node['realText']}</{node['nodeName']}>")

        elif "styles" in node:
            node["output"] = []
            unlist = []
            for cssProperty, cssValue in node["styles"].items():
                unlist.append(f"{cssProperty}: {cssValue}; ")
            joined = "".join(unlist)
            node["output"].append(f"#i{node['index']} {{{joined}}}")
            
            if "realText" in node:
                node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}'>{node['realText']}</{node['nodeName']}>")
            else:
                node["output"].insert(0, f"<{node['nodeName']} id='i{node['index']}'>place</{node['nodeName']}>")
        else:
            node["filler"] = []
            node["filler"].append(f"<{node['nodeName']}></{node['nodeName']}>")
    
    with open("customDoc.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(customDoc, indent=2))

    def swap(pIndex, ppIndex):
        for node in customDoc:
            if node["parentIndex"] == pIndex:
                node["parentIndex"] = ppIndex


    for node in customDoc:
        if node["nodeName"] == "g":
            swap(node["index"], node["parentIndex"])

    
    def connect(index):
        for node in customDoc:
            if node["parentIndex"] == index and not "marked" in node:
                if "styles" in node:
                    if "childNodes" in customDoc[index]:
                        customDoc[index]["childNodes"].append(node["output"][0])
                        node["marked"] = "marked"
                    else:
                        customDoc[index]["childNodes"] = []
                        customDoc[index]["childNodes"].append(node["output"][0])
                        node["marked"] = "marked"
                else:
                    continue
            else:
                continue
    
    for node in customDoc:
        if node["nodeName"] == "svg":
            connect(node["index"])

    
    for node in customDoc:
        if "childNodes" in node:
            joined = "\n    ".join(node["childNodes"])
            node["output"][0] = node["output"][0].replace("place", joined)

    
    elementList = []

    for node in customDoc:
        if node["nodeType"] == 1 and not node["nodeName"].startswith(":") and node["nodeName"] != "script" and node["nodeName"] != "style" and node["nodeName"] != "iframe" and node["nodeName"] != "html" and node["nodeName"] != "head" and "styles" in node and node["nodeName"] != "ul" and node["nodeName"] != "li" and node["nodeName"] != "body":
            elementList.append(node)

    
    for node in elementList:
        o = node["output"][0]
        if "place" in node["output"][0]:
            node["output"][0] = node["output"][0].replace("place", "")
        else:
            continue


    with open("index.html", "w", encoding="utf-8") as htmlFile, open("stylesheet.css", "w", encoding="utf-8") as cssFile:

        htmlFile.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="stylesheet.css">
</head>
<body>                  
""")
        cssFile.write("body {overflow-x: hidden;}" + "\n")

        for node in elementList:
            if "marked" in node:
                cssFile.write(node["output"][1] + "\n")
            elif "inlineStyles" in node:
                htmlFile.write(node["output"][0] + "\n")
                htmlFile.write(node["output"][1] + "\n")
                cssFile.write(node["output"][2] + "\n")
                cssFile.write(node["output"][3] + "\n")
            else:
                htmlFile.write(node["output"][0] + "\n")
                cssFile.write(node["output"][1] + "\n")

        
        htmlFile.write("""
</body>
</html>
""")
                       
                    





  

